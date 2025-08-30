import os
import json
from pathlib import Path
from PIL import Image
from super_image import EdsrModel, ImageLoader

def load_config():
    """Loads the configuration from config.json."""
    config_path = Path('config.json')
    if not config_path.exists():
        print("Error: config.json not found. Please create it.")
        return None
    with open(config_path, 'r') as f:
        return json.load(f)

def get_image_paths(input_path):
    """Gets a list of image file paths from a single file or a directory."""
    input_path = Path(input_path)
    image_paths = []
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']

    if input_path.is_dir():
        print(f"Processing folder: {input_path}")
        for file_path in sorted(input_path.iterdir()):
            if file_path.suffix.lower() in supported_formats:
                image_paths.append(file_path)
    elif input_path.is_file():
        if input_path.suffix.lower() in supported_formats:
            print(f"Processing single image: {input_path}")
            image_paths.append(file_path)
    
    return image_paths

def upscale_image(image_path, model, config):
    """Upscales a single image and saves it."""
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return

    print(f"Upscaling {image_path.name}...")
    
    inputs = ImageLoader.load_image(image)
    preds = model(inputs)

    export_path = Path(config.get('export_path', 'images/output'))
    export_format = config.get('export_format', 'png')
    export_path.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{image_path.stem}_upscaled.{export_format}"
    output_path = export_path / output_filename

    mode = config.get('resolution_mode', 'multiplier')
    value = config.get('resolution_value', 2)

    if mode == 'fixed':
        try:
            width, height = map(int, str(value).split('x'))
            preds = preds.resize((width, height), Image.Resampling.LANCZOS)
            print(f"Resizing to fixed resolution: {width}x{height}")
        except (ValueError, TypeError):
            print(f"Warning: Invalid 'fixed' resolution value '{value}'. Using multiplier instead.")

    ImageLoader.save_image(preds, output_path)
    print(f"Successfully saved upscaled image to: {output_path}")


def main():
    """Main function to run the upscaler."""
    config = load_config()
    if not config:
        return

    # Prepare directories
    import_path_str = config.get('import_path', 'images/input')
    export_path_str = config.get('export_path', 'images/output')
    Path(import_path_str).mkdir(parents=True, exist_ok=True)
    Path(export_path_str).mkdir(parents=True, exist_ok=True)

    scale = 2
    if config.get('resolution_mode') == 'multiplier':
        try:
            scale = int(config.get('resolution_value', 2))
        except (ValueError, TypeError):
            print("Warning: Invalid 'multiplier' value in config. Defaulting to 2.")
            scale = 2
            
    model_name = config.get('model_name', 'eugenesiow/edsr-base')
    print(f"Loading model: {model_name} with scale x{scale}...")
    try:
        model = EdsrModel.from_pretrained(model_name, scale=scale)
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please ensure the model name and scale in config.json are correct.")
        return

    print("Model loaded successfully.")

    while True:
        default_import_path = config.get('import_path', 'images/input')
        user_input = input(f"Enter the path to an image or folder (or type 'exit' to quit) [{default_import_path}]: ")

        if user_input.lower() in ['exit', 'quit']:
            break
        
        if not user_input:
            user_input = default_import_path

        input_path = Path(user_input)

        if not input_path.exists():
            print(f"Error: The path '{user_input}' does not exist. Please try again.")
            continue

        image_paths = get_image_paths(user_input)

        if not image_paths:
            print(f"No supported image files found at '{user_input}'. Supported formats: .png, .jpg, .jpeg, .bmp, .tiff")
            continue

        for path in image_paths:
            upscale_image(path, model, config)
        
        print("\nProcessing complete for this batch.")
        
        another = input("Process another file or folder? (y/n): ")
        if another.lower() != 'y':
            break

if __name__ == "__main__":
    main()
