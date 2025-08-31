from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from src.upscaler import upscale_image as upscale_image_processor, load_config
from super_image import EdsrModel

app = Flask(__name__, static_folder='static')

# Load configuration
config = load_config()
app.config['UPLOAD_FOLDER'] = config.get('import_path', 'images/input')
app.config['OUTPUT_FOLDER'] = config.get('export_path', 'images/output')

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)

# Cache for loaded models
loaded_models = {}

def get_model(model_name, scale):
    """Loads a model or retrieves it from cache."""
    model_key = f"{model_name}_{scale}"
    if model_key not in loaded_models:
        print(f"Loading model: {model_name} with scale x{scale}...")
        try:
            loaded_models[model_key] = EdsrModel.from_pretrained(model_name, scale=scale)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return loaded_models[model_key]

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/config')
def get_config():
    """Provides the initial configuration to the frontend."""
    return jsonify(config)

@app.route('/outputs/<filename>')
def uploaded_file(filename):
    """Serves upscaled images from the output directory."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/upscale', methods=['POST'])
def upscale():
    """Handles image upload and the upscaling process."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        upload_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(upload_path)

        try:
            # Get settings from the form
            scale = int(request.form.get('resolution_value', 2))
            model_name = request.form.get('model_name', config.get('model_name'))

            # Prepare a temporary config for the upscaler function
            upscale_config = {
                'export_path': app.config['OUTPUT_FOLDER'],
                'export_format': request.form.get('export_format', 'png'),
                'resolution_mode': request.form.get('resolution_mode', 'multiplier'),
                'resolution_value': scale
            }

            # Get the model
            model = get_model(model_name, scale)
            if not model:
                return jsonify({'error': 'Failed to load the specified model.'}), 500

            # Run the upscaler
            output_path = upscale_image_processor(upload_path, model, upscale_config)

            if output_path:
                # The path returned is a Path object, convert to string for URL
                output_filename = os.path.basename(output_path)
                return jsonify({'output_path': f'/outputs/{output_filename}'})
            else:
                return jsonify({'error': 'Failed to upscale image.'}), 500

        except Exception as e:
            print(f"An error occurred during upscaling: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'An unknown error occurred.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
