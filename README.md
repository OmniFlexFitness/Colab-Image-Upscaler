# Local Image Upscaler

This project uses the `super-image` library to upscale images locally. It uses a pre-trained EDSR (Enhanced Deep Residual Networks for Single Image Super-Resolution) model to enhance image resolution, with settings managed through a configuration file.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/OmniFlexFitness/Colab-Image-Upscaler.git
    cd Colab-Image-Upscaler
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    Install the required packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running the upscaler, you can customize its behavior by editing the `config.json` file.

```json
{
  "import_path": "images/input",
  "export_path": "images/output",
  "export_format": "png",
  "resolution_mode": "multiplier",
  "resolution_value": 2,
  "model_name": "eugenesiow/edsr-base",
  "other_flags": {
    "face_enhance": false
  },
  "notes": {
    "resolution_mode": "Use 'multiplier' (e.g., 2, 4) or 'fixed' (e.g., '1920x1080').",
    "face_enhance": "This flag is not currently supported by the super-image library but is included for future compatibility."
  }
}
```

*   `import_path`: The default folder where the script will look for images. If the folder doesn't exist, it will be created.
*   `export_path`: The folder where upscaled images will be saved. If the folder doesn't exist, it will be created.
*   `export_format`: The output file format for upscaled images (e.g., `png`, `jpg`).
*   `resolution_mode`: Set to `"multiplier"` to scale by a factor (e.g., 2x, 4x) or `"fixed"` to resize to a specific resolution.
*   `resolution_value`: The value for the chosen mode. For `multiplier`, this is a number (e.g., `2`). For `fixed`, this is a string (e.g., `"1920x1080"`).
*   `model_name`: The pre-trained model to use from the Hugging Face Hub.

## Usage

The application can be run using the provided scripts. It will prompt you to enter a path to an image or a folder of images.

1.  **For Windows:**
    Double-click `Upscaler.bat` or run it from the command line:
    ```cmd
    Upscaler.bat
    ```

2.  **For macOS/Linux:**
    Run the shell script from your terminal:
    ```bash
    ./Upscaler.sh
    ```

The script will prompt you for the path to your image or folder. You can press Enter to use the default `import_path` from your `config.json`. If the path is invalid, it will ask you to try again. The script can handle single image files or a folder containing multiple images.
