document.addEventListener('DOMContentLoaded', () => {
    const settingsForm = document.getElementById('settings-form');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const upscaleButton = document.getElementById('upscale-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultImageContainer = document.getElementById('result-image-container');
    const outputDirectoryInput = document.getElementById('output_directory');

    // Fetch and apply initial config
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            document.getElementById('export_format').value = config.export_format || 'png';
            document.getElementById('resolution_mode').value = config.resolution_mode || 'multiplier';
            document.getElementById('resolution_value').value = config.resolution_value || 2;
            document.getElementById('model_name').value = config.model_name || 'eugenesiow/edsr-base';
            outputDirectoryInput.placeholder = `Default: ${config.export_path || 'images/output'}`;
        })
        .catch(error => console.error('Error fetching config:', error));

    // Updated image preview logic
    imageUpload.addEventListener('change', () => {
        imagePreview.innerHTML = '';
        imagePreview.classList.remove('single-image', 'multi-image');

        if (imageUpload.files.length === 1) {
            imagePreview.classList.add('single-image');
        } else if (imageUpload.files.length > 1) {
            imagePreview.classList.add('multi-image');
        }

        if (imageUpload.files.length > 0) {
            for (const file of imageUpload.files) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const imgContainer = document.createElement('div');
                    imgContainer.className = 'preview-image-container';
                    imgContainer.innerHTML = `<img src="${e.target.result}" alt="Image Preview">
                                            <div class="image-filename">${file.name}</div>`;
                    imagePreview.appendChild(imgContainer);
                };
                reader.readAsDataURL(file);
            }
        }
    });

    // Upscale button click
    upscaleButton.addEventListener('click', () => {
        if (imageUpload.files.length === 0) {
            alert('Please select at least one image first.');
            return;
        }

        loadingIndicator.style.display = 'block';
        resultImageContainer.innerHTML = '';

        const formData = new FormData(settingsForm);
        for (const file of imageUpload.files) {
            formData.append('image', file);
        }

        fetch('/upscale', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'An unknown error occurred.') });
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.style.display = 'none';
            if (data.results) {
                displayResults(data.results);
            } else {
                throw new Error(data.error || 'An unknown error occurred.');
            }
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            alert(`Error: ${error.message}`);
            console.error('Upscale error:', error);
        });
    });

    function displayResults(results) {
        resultImageContainer.innerHTML = '<h3>Upscaled Images:</h3>';

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            if (result.output_path) {
                const filename = result.output_path.split(/[\\/]/).pop();
                const imageUrl = `${result.output_path}?output_dir=${encodeURIComponent(result.output_dir)}&t=${new Date().getTime()}`;

                resultDiv.className = 'result-item';
                resultDiv.innerHTML = `
                    <h4>${result.original}</h4>
                    <div class="result-image">
                        <img src="${imageUrl}" alt="Upscaled ${result.original}">
                    </div>
                    <a href="${imageUrl}" download="${filename}" class="download-button button">Download</a>
                `;
            } else {
                resultDiv.className = 'result-item error';
                resultDiv.innerHTML = `
                    <h4>${result.original}</h4>
                    <p class="error-message">Error: ${result.error}</p>
                `;
            }
            resultImageContainer.appendChild(resultDiv);
        });
    }
});
