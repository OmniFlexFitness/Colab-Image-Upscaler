document.addEventListener('DOMContentLoaded', () => {
    const settingsForm = document.getElementById('settings-form');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const upscaleButton = document.getElementById('upscale-button');
    const cancelButton = document.getElementById('cancel-button');
    const resultImageContainer = document.getElementById('result-image-container');

    // New UI elements
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const currentFileText = document.getElementById('current-file-text');
    const outputDirectoryInput = document.getElementById('output_directory');

    let currentGroupId = null;
    let pollInterval = null;

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

    // Upscale button click for Celery
    upscaleButton.addEventListener('click', () => {
        if (imageUpload.files.length === 0) {
            alert('Please select at least one image first.');
            return;
        }

        // Reset UI
        resultImageContainer.innerHTML = '';
        progressContainer.style.display = 'block';
        upscaleButton.style.display = 'none';
        cancelButton.style.display = 'inline-block';
        
        const formData = new FormData(settingsForm);
        for (const file of imageUpload.files) {
            formData.append('image', file);
        }

        // Start the upscale job
        fetch('/upscale/start', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            currentGroupId = data.group_id;
            pollInterval = setInterval(pollJobStatus, 1000);
        })
        .catch(error => {
            alert(`Error starting job: ${error.message}`);
            resetUi();
        });
    });

    function pollJobStatus() {
        if (!currentGroupId) return;

        fetch(`/upscale/status/${currentGroupId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                const { total, completed_count, results } = data;
                
                const percent = total > 0 ? (completed_count / total) * 100 : 0;
                progressBar.style.width = `${percent}%`;
                progressText.textContent = `Processing: ${completed_count} / ${total}`;
                currentFileText.textContent = `Progress: ${Math.round(percent)}%`;


                if (completed_count === total) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    currentGroupId = null;
                    displayResults(results, outputDirectoryInput.value || '');
                    resetUi();
                }
            })
            .catch(error => {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
                alert(`Error checking job status: ${error.message}`);
                resetUi();
            });
    }

    function displayResults(results, outputDir) {
        progressContainer.style.display = 'none';
        resultImageContainer.innerHTML = '<h3>Upscaled Images:</h3>';

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            if (result.status === 'SUCCESS') {
                const filename = result.output_path.split(/[\\/]/).pop();
                const imageUrl = `/outputs/${filename}?output_dir=${encodeURIComponent(outputDir)}&t=${new Date().getTime()}`;

                resultDiv.className = 'result-item';
                resultDiv.innerHTML = `
                    <h4>${result.original}</h4>
                    <div class="result-image">
                        <img src="${imageUrl}" alt="Upscaled ${result.original}">
                    </div>
                    <a href="${imageUrl}" download="${filename}" class="download-button">Download</a>
                `;
            } else {
                resultDiv.className = 'result-item error';
                resultDiv.innerHTML = `
                    <h4>${result.original || 'Unknown file'}</h4>
                    <p class="error-message">Error: ${result.error || 'An unknown error occurred.'}</p>
                `;
            }
            resultImageContainer.appendChild(resultDiv);
        });
    }

    cancelButton.addEventListener('click', () => {
        if (!currentGroupId) return;

        fetch(`/upscale/cancel/${currentGroupId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                clearInterval(pollInterval);
                alert('Upscaling was cancelled.');
                resetUi();
            })
            .catch(error => console.error('Error cancelling job:', error));
    });

    function resetUi() {
        upscaleButton.style.display = 'inline-block';
        cancelButton.style.display = 'none';
        progressContainer.style.display = 'none';
        progressBar.style.width = '0%';
        progressText.textContent = '';
        currentFileText.textContent = '';
    }
});
