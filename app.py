from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from src.upscaler import upscale_image as upscale_image_processor, load_config
from src.video_processor import extract_frames
from super_image import EdsrModel

app = Flask(__name__, static_folder='static')

# Load configuration
config = load_config()
app.config['UPLOAD_FOLDER'] = config.get('import_path', 'images/input')
app.config['OUTPUT_FOLDER'] = config.get('export_path', 'images/output')
app.config['TEMP_VIDEO_FOLDER'] = 'images/temp_videos'


# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['TEMP_VIDEO_FOLDER']).mkdir(parents=True, exist_ok=True)

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
    output_dir = request.args.get('output_dir', app.config['OUTPUT_FOLDER'])
    return send_from_directory(output_dir, filename)

@app.route('/extract', methods=['POST'])
def extract():
    """Handles video upload, frame extraction, and optional upscaling."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(video_file.filename)
    temp_video_path = Path(app.config['TEMP_VIDEO_FOLDER']) / filename
    video_file.save(temp_video_path)

    form_data = request.form.to_dict()
    should_upscale = form_data.get('upscale_frames') == 'true'

    # Extract frames into the main input folder
    extracted_frames, _ = extract_frames(temp_video_path, Path(app.config['UPLOAD_FOLDER']), should_upscale, Path(app.config['OUTPUT_FOLDER']))

    results = {'extracted_count': len(extracted_frames), 'upscaled_results': []}

    if should_upscale:
        # Most of the upscaling logic is similar to the /upscale route
        output_dir = form_data.get('output_directory') or app.config['OUTPUT_FOLDER']
        if output_dir:
            output_dir = output_dir.strip('\'"')
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        try:
            scale = int(form_data.get('resolution_value'))
        except (ValueError, TypeError):
            scale = 2  # default

        model_name = form_data.get('model_name', config.get('model_name'))
        model = get_model(model_name, scale)

        if not model:
            return jsonify({'error': 'Failed to load the specified model.'}), 500

        upscale_config = {
            'export_path': output_dir,
            'export_format': form_data.get('export_format', 'png'),
            'resolution_mode': form_data.get('resolution_mode', 'multiplier'),
            'resolution_value': form_data.get('resolution_value')
        }

        for frame_path in extracted_frames:
            try:
                output_path = upscale_image_processor(frame_path, model, upscale_config)
                if output_path:
                    output_filename = os.path.basename(output_path)
                    results['upscaled_results'].append({'original': frame_path.name, 'output_path': f'/outputs/{output_filename}', 'output_dir': output_dir})
                else:
                    results['upscaled_results'].append({'original': frame_path.name, 'error': 'Failed to upscale frame.'})
            except Exception as e:
                print(f"An error occurred during upscaling {frame_path.name}: {e}")
                results['upscaled_results'].append({'original': frame_path.name, 'error': str(e)})

    # Clean up the temporary video file
    os.remove(temp_video_path)

    return jsonify(results)

@app.route('/upscale', methods=['POST'])
def upscale():
    """Handles multiple image uploads and the upscaling process."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400

    files = request.files.getlist('image')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No selected files'}), 400

    results = []
    form_data = request.form.to_dict()
    output_dir = form_data.get('output_directory') or app.config['OUTPUT_FOLDER']

    if output_dir:
        output_dir = output_dir.strip('\'"')

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_path = Path(app.config['UPLOAD_FOLDER']) / filename
            file.save(upload_path)

            try:
                # This is a bit of a hack to handle the fact that the form value is a string
                try:
                    scale = int(form_data.get('resolution_value'))
                except (ValueError, TypeError):
                    scale = 2 # default

                model_name = form_data.get('model_name', config.get('model_name'))

                upscale_config = {
                    'export_path': output_dir,
                    'export_format': form_data.get('export_format', 'png'),
                    'resolution_mode': form_data.get('resolution_mode', 'multiplier'),
                    'resolution_value': form_data.get('resolution_value')
                }

                model = get_model(model_name, scale)
                if not model:
                    results.append({'original': filename, 'error': 'Failed to load the specified model.'})
                    continue

                output_path = upscale_image_processor(upload_path, model, upscale_config)

                if output_path:
                    output_filename = os.path.basename(output_path)
                    results.append({'original': filename, 'output_path': f'/outputs/{output_filename}', 'output_dir': output_dir})
                else:
                    results.append({'original': filename, 'error': 'Failed to upscale image.'})

            except Exception as e:
                print(f"An error occurred during upscaling {filename}: {e}")
                results.append({'original': filename, 'error': str(e)})

    if not results:
        return jsonify({'error': 'No files were processed successfully.'}), 500

    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)