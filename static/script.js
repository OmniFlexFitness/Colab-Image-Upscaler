document.addEventListener('DOMContentLoaded', () => {
    // Mode selection
    const imageModeRadio = document.querySelector('input[name="mode"][value="image"]');
    const videoModeRadio = document.querySelector('input[name="mode"][value="video"]');
    const imageModeSection = document.getElementById('image-mode-section');
    const videoModeSection = document.getElementById('video-mode-section');
    const videoSettings = document.getElementById('video-settings');

    // General elements
    const settingsForm = document.getElementById('settings-form');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultImageContainer = document.getElementById('result-image-container');
    const outputDirectoryInput = document.getElementById('output_directory');
    const actionButton = document.getElementById('action-button');
    const actionTitle = document.getElementById('action-title');

    // Image-specific elements
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');

    // Video-specific elements
    const videoUpload = document.getElementById('video-upload');
    const videoPreview = document.getElementById('video-preview');
    const upscaleFramesCheckbox = document.getElementById('upscale_frames');

    // --- Initial Setup ---
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

    // --- Mode Switching Logic ---
    function updateMode() {
        if (imageModeRadio.checked) {
            imageModeSection.style.display = 'block';
            videoModeSection.style.display = 'none';
            videoSettings.style.display = 'none';
            actionTitle.textContent = '3. Upscale';
            actionButton.textContent = 'Upscale Image(s)';
            clearPreviews();
        } else {
            imageModeSection.style.display = 'none';
            videoModeSection.style.display = 'block';
            videoSettings.style.display = 'block';
            actionTitle.textContent = '3. Process Video';
            actionButton.textContent = 'Extract Frames';
            clearPreviews();
        }
    }

    imageModeRadio.addEventListener('change', updateMode);
    videoModeRadio.addEventListener('change', updateMode);
    updateMode(); // Set initial mode

    // --- Preview Logic ---
    function clearPreviews() {
        imagePreview.innerHTML = '';
        videoPreview.innerHTML = '';
        imageUpload.value = '';
        videoUpload.value = '';
    }

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

    videoUpload.addEventListener('change', () => {
        videoPreview.innerHTML = '';
        if (videoUpload.files.length > 0) {
            const file = videoUpload.files[0];
            const videoElement = document.createElement('video');
            videoElement.src = URL.createObjectURL(file);
            videoElement.controls = true;
            videoElement.style.maxWidth = '100%';
            videoPreview.appendChild(videoElement);
        }
    });

    // --- Action Button Logic ---
    actionButton.addEventListener('click', () => {
        if (imageModeRadio.checked) {
            handleImageUpscale();
        } else {
            handleVideoExtract();
        }
    });

    function handleImageUpscale() {
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
                displayImageResults(data.results);
            } else {
                throw new Error(data.error || 'An unknown error occurred.');
            }
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            alert(`Error: ${error.message}`);
            console.error('Upscale error:', error);
        });
    }

    function handleVideoExtract() {
        if (videoUpload.files.length === 0) {
            alert('Please select a video file first.');
            return;
        }

        loadingIndicator.style.display = 'block';
        resultImageContainer.innerHTML = '';

        const formData = new FormData(settingsForm);
        formData.append('video', videoUpload.files[0]);
        formData.set('upscale_frames', upscaleFramesCheckbox.checked);


        fetch('/extract', {
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
            displayVideoResults(data);
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            alert(`Error: ${error.message}`);
            console.error('Extraction error:', error);
        });
    }

    // --- Result Display Logic ---
    function displayImageResults(results) {
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

    function displayVideoResults(data) {
        resultImageContainer.innerHTML = `<h3>Extraction Complete</h3>
                                          <p>${data.extracted_count} frames were extracted.</p>`;
        if (data.upscaled_results && data.upscaled_results.length > 0) {
            resultImageContainer.innerHTML += '<h3>Upscaled Frames:</h3>';
            displayImageResults(data.upscaled_results); // Reuse the same display logic
        }
    }
});
