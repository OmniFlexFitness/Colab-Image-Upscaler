import json
from pathlib import Path
from PIL import Image
from super_image import ImageLoader

def load_config():
    """Loads the configuration from config.json."""
    config_path = Path('config.json')
    if not config_path.exists():
        # This is a fallback, but app.py should handle it.
        print("Warning: config.json not found. Using default settings.")
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)

def upscale_image(image_path: Path, model, config: dict) -> Path:
    """
    Upscales a single image using a pre-loaded model and returns the path to the saved file.

    Args:
        image_path: Path to the input image.
        model: The pre-loaded EdsrModel instance.
        config: A dictionary with 'export_path', 'export_format', 'resolution_mode', etc.

    Returns:
        The path to the upscaled image file, or None if an error occurred.
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None

    print(f"Upscaling {image_path.name}...")
    
    # The model is already loaded, so we can use it directly.
    inputs = ImageLoader.load_image(image)
    preds = model(inputs)

    # Get settings from the passed config dictionary
    export_path = Path(config.get('export_path', 'images/output'))
    export_format = config.get('export_format', 'png')
    export_path.mkdir(parents=True, exist_ok=True)

    mode = config.get('resolution_mode', 'multiplier')
    value = config.get('resolution_value')
    
    # Create a unique filename to avoid conflicts
    base_filename = image_path.stem
    counter = 0
    output_filename = f"{base_filename}_{value}x.{export_format}"
    output_path = export_path / output_filename

    while output_path.exists():
        counter += 1
        output_filename = f"{base_filename}_{value}x_{counter}.{export_format}"
        output_path = export_path / output_filename


    if mode == 'fixed' and value:
        try:
            # For fixed resolution, we resize after upscaling
            # This is not ideal but matches the original logic's intent.
            # A better approach would be a different model or pre-resize.
            width, height = map(int, str(value).split('x'))
            preds = preds.resize((width, height), Image.Resampling.LANCZOS)
            print(f"Resizing to fixed resolution: {width}x{height}")
        except (ValueError, TypeError):
            print(f"Warning: Invalid 'fixed' resolution value '{value}'. Ignoring.")

    ImageLoader.save_image(preds, output_path)
    print(f"Successfully saved upscaled image to: {output_path}")

    return output_path
