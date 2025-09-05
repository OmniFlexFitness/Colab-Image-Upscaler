document.addEventListener('DOMContentLoaded', () => {
    const settingsForm = document.getElementById('settings-form');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const upscaleButton = document.getElementById('upscale-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultImageContainer = document.getElementById('result-image-container');
    const downloadLink = document.getElementById('download-link');

    // Fetch and apply initial config
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            document.getElementById('export_format').value = config.export_format || 'png';
            document.getElementById('resolution_mode').value = config.resolution_mode || 'multiplier';
            document.getElementById('resolution_value').value = config.resolution_value || 2;
            document.getElementById('model_name').value = config.model_name || 'eugenesiow/edsr-base';
        })
        .catch(error => console.error('Error fetching config:', error));

    // Multiple images preview
    imageUpload.addEventListener('change', () => {
        imagePreview.innerHTML = '';
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
        downloadLink.style.display = 'none';

        const formData = new FormData();
        
        // Append all selected files to the form data
        for (const file of imageUpload.files) {
            formData.append('image', file);
        }

        // Append form settings
        const settings = new FormData(settingsForm);
        for (const [key, value] of settings.entries()) {
            formData.append(key, value);
        }
        fetch('/upscale', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.style.display = 'none';
            if (data.results) {
                // Display all results
                resultImageContainer.innerHTML = '<h3>Upscaled Images:</h3>';
                
                data.results.forEach(result => {
                    if (result.output_path) {
                        const imageUrl = `${result.output_path}?t=${new Date().getTime()}`;
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-item';
                        resultDiv.innerHTML = `
                            <h4>${result.original}</h4>
                            <div class="result-image">
                                <img src="${imageUrl}" alt="Upscaled ${result.original}">
                            </div>
                            <a href="${imageUrl}" download="${result.output_path.split('/').pop()}" class="download-button">Download</a>
                        `;
                        resultImageContainer.appendChild(resultDiv);
                    } else if (result.error) {
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-item error';
                        resultDiv.innerHTML = `
                            <h4>${result.original}</h4>
                            <p class="error-message">Error: ${result.error}</p>
                        `;
                        resultImageContainer.appendChild(resultDiv);
                    }
                });
                
                // Hide the single download link as we now have multiple download buttons
                downloadLink.style.display = 'none';
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
});
