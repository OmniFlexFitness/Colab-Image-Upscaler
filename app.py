from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from src.upscaler import load_config
from celery_app import celery, upscale_image_task
from celery import group
from celery.result import GroupResult
import subprocess
import atexit
import sys

app = Flask(__name__, static_folder='static')

# Load configuration
config = load_config()
app.config['UPLOAD_FOLDER'] = config.get('import_path', 'images/input')
app.config['OUTPUT_FOLDER'] = config.get('export_path', 'images/output')

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)

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
    # The output directory might change per-request, so we need to handle this.
    # For simplicity, we assume all outputs go to the default or a specified folder.
    # A robust implementation might need to know the job_id.
    output_dir = request.args.get('output_dir', app.config['OUTPUT_FOLDER'])
    return send_from_directory(output_dir, filename)

@app.route('/upscale/start', methods=['POST'])
def upscale_start():
    """Starts the upscaling process in the background using Celery."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400

    files = request.files.getlist('image')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No selected files'}), 400

    # Get settings from the form
    form_data = request.form.to_dict()
    output_dir = form_data.get('output_directory') or app.config['OUTPUT_FOLDER']
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tasks = []
    for file in files:
        filename = secure_filename(file.filename)
        upload_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(upload_path)
        # Each task is a signature of the upscale_image_task
        tasks.append(upscale_image_task.s(str(upload_path), form_data, output_dir))

    # Create a group of tasks to run them in parallel
    task_group = group(tasks)
    result_group = task_group.apply_async()

    # Save the group result to check status later
    result_group.save()

    return jsonify({'group_id': result_group.id})

@app.route('/upscale/status/<group_id>')
def upscale_status(group_id):
    """Gets the status of a Celery task group."""
    result = GroupResult.restore(group_id, app=celery)

    if not result:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'total': len(result.results),
        'completed_count': result.completed_count(),
        'results': [r.get() for r in result.results if r.successful()]
    })

@app.route('/upscale/cancel/<group_id>', methods=['POST'])
def upscale_cancel(group_id):
    """Cancels all tasks in a Celery task group."""
    result = GroupResult.restore(group_id, app=celery)
    if result:
        result.revoke(terminate=True)
        return jsonify({'message': 'Cancellation request sent.'})
    return jsonify({'error': 'Job not found'}), 404

celery_worker_process = None

def start_celery_worker():
    """Starts a Celery worker in a background process."""
    global celery_worker_process
    command = [
        sys.executable,  # Use the current python interpreter
        '-m', 'celery',    # Run celery as a module
        '-A', 'celery_app.celery',
        'worker',
        '--loglevel=info'
    ]
    celery_worker_process = subprocess.Popen(command)
    print("Celery worker started with PID:", celery_worker_process.pid)

def stop_celery_worker():
    """Stops the background Celery worker."""
    global celery_worker_process
    if celery_worker_process:
        celery_worker_process.terminate()
        celery_worker_process.wait()
        print("Celery worker stopped.")

if __name__ == '__main__':
    start_celery_worker()
    atexit.register(stop_celery_worker)
    app.run(host='0.0.0.0', port=8084)