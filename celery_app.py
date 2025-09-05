from celery import Celery
from pathlib import Path
import os
from src.upscaler import upscale_image as upscale_image_processor, load_config
from super_image import EdsrModel

# Ensure the data directories for Celery exist
base_dir = Path(__file__).parent
broker_dir = base_dir / '.celery-data' / 'broker'
results_dir = base_dir / '.celery-data' / 'results'
broker_dir.mkdir(parents=True, exist_ok=True)
results_dir.mkdir(parents=True, exist_ok=True)

# Create and configure the Celery application
celery = Celery(
    __name__,
    broker=f'filesystem://',
    backend=f'file://{results_dir}',
    broker_transport_options={
        'data_folder_in': str(broker_dir),
        'data_folder_out': str(broker_dir),
    }
)

# Load the main config to get model details
config = load_config()

# Global cache for loaded models in the worker
loaded_models = {}

@celery.task(bind=True)
def upscale_image_task(self, image_path_str, form_data, output_dir):
    """Celery task to upscale a single image."""
    try:
        image_path = Path(image_path_str)

        # Get model and scale from form_data
        scale = int(form_data.get('resolution_value', 2))
        model_name = form_data.get('model_name', config.get('model_name'))

        # Check cache for model, load if not present
        model_key = f"{model_name}_{scale}"
        if model_key not in loaded_models:
            print(f"Loading model in worker: {model_name} with scale x{scale}...")
            loaded_models[model_key] = EdsrModel.from_pretrained(model_name, scale=scale)

        model = loaded_models.get(model_key)
        if not model:
            raise Exception("Failed to load model in Celery worker.")

        # Prepare config for the upscaler function
        upscale_config = {
            'export_path': output_dir,
            'export_format': form_data.get('export_format', 'png'),
            'resolution_mode': form_data.get('resolution_mode', 'multiplier'),
            'resolution_value': scale
        }

        # Run the actual upscaling function
        output_path = upscale_image_processor(image_path, model, upscale_config)

        if output_path:
            return {
                'status': 'SUCCESS',
                'original': image_path.name,
                'output_path': str(output_path)
            }
        else:
            raise Exception("Upscaling failed to produce an output file.")

    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        # It's good practice to re-raise the exception
        raise e
