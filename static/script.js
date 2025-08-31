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

    // Image preview
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.innerHTML = `<img src="${e.target.result}" alt="Image Preview">`;
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.innerHTML = '';
        }
    });

    // Upscale button click
    upscaleButton.addEventListener('click', () => {
        if (!imageUpload.files[0]) {
            alert('Please select an image first.');
            return;
        }

        loadingIndicator.style.display = 'block';
        resultImageContainer.innerHTML = '';
        downloadLink.style.display = 'none';

        const formData = new FormData();
        formData.append('image', imageUpload.files[0]);

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
            if (data.output_path) {
                const imageUrl = `${data.output_path}?t=${new Date().getTime()}`;
                resultImageContainer.innerHTML = `<img src="${imageUrl}" alt="Upscaled Image">`;
                downloadLink.href = imageUrl;
                downloadLink.download = data.output_path.split('/').pop();
                downloadLink.style.display = 'block';
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
