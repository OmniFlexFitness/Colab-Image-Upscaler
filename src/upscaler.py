import os
import json
from pathlib import Path
from PIL import Image
from super_image import EdsrModel, ImageLoader
from video_processing import process_video

def load_config():
    """Loads the configuration from config.json."""
    config_path = Path('config.json')
    if not config_path.exists():
        print("Error: config.json not found. Please create it.")
        return None
    with open(config_path, 'r') as f:
        return json.load(f)

def get_media_paths(input_path):
    """Gets lists of image and video file paths from a single file or a directory."""
    input_path = Path(input_path)
    image_paths = []
    video_paths = []
    supported_image_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    supported_video_formats = ['.mp4', '.mov', '.avi', '.mkv']

    if input_path.is_dir():
        print(f"Scanning folder: {input_path}")
        for file_path in sorted(input_path.iterdir()):
            if file_path.suffix.lower() in supported_image_formats:
                image_paths.append(file_path)
            elif file_path.suffix.lower() in supported_video_formats:
                video_paths.append(file_path)
    elif input_path.is_file():
        if input_path.suffix.lower() in supported_image_formats:
            image_paths.append(input_path)
        elif input_path.suffix.lower() in supported_video_formats:
            video_paths.append(input_path)
    
    return image_paths, video_paths

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
        user_input = input(f"Enter the path to a media file or folder (or type 'exit' to quit) [{default_import_path}]: ")

        if user_input.lower() in ['exit', 'quit']:
            break
        
        if not user_input:
            user_input = default_import_path

        input_path = Path(user_input)

        if not input_path.exists():
            print(f"Error: The path '{user_input}' does not exist. Please try again.")
            continue

        image_paths, video_paths = get_media_paths(user_input)

        if not image_paths and not video_paths:
            print(f"No supported media files found at '{user_input}'.")
            continue
        
        media_type_to_process = "all"
        if image_paths and video_paths and input_path.is_dir():
            while True:
                choice = input("Both images and videos found. What would you like to process? (images/videos/all): ").lower()
                if choice in ["images", "videos", "all"]:
                    media_type_to_process = choice
                    break
                else:
                    print("Invalid choice. Please enter 'images', 'videos', or 'all'.")

        if media_type_to_process in ["images", "all"]:
            for path in image_paths:
                upscale_image(path, model, config)

        if media_type_to_process in ["videos", "all"]:
            for path in video_paths:
                process_video(path, config, model)
        
        print("\nProcessing complete for this batch.")
        
        another = input("Process another file or folder? (y/n): ")
        if another.lower() != 'y':
            break

if __name__ == "__main__":
    main()
