# OmniFlex Image Upscaler

This project provides a web-based graphical user interface (GUI) for upscaling images using pre-trained EDSR (Enhanced Deep Residual Networks for Single Image Super-Resolution) models.

## Features

-   **Web-based GUI:** Easy-to-use interface for uploading and processing images.
-   **Enhanced Image Previews:**
    -   Single images are shown with a max height of `50vh`.
    -   Multiple images are displayed in a scrollable, Pinterest-style waterfall grid.
-   **Custom Output Directory:** Specify a custom folder to save your upscaled images.
-   **Custom Filename:** The output filename includes the upscaling factor (e.g., `_2x` or `_1920x1080`).

## Setup and Installation

Follow these steps to set up and run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/OmniFlexFitness/Colab-Image-Upscaler.git
cd Colab-Image-Upscaler
```

### 2. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Install all required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## Running the Application

Once the setup is complete, you can run the application with a single command.

```bash
python app.py
```

The application will be available at: **http://127.0.0.1:8084** (or the port specified in `app.py`).

## Configuration

You can customize the default upscaling settings by editing the `config.json` file. These settings can also be overridden in the web UI.

```json
{
  "import_path": "images/input",
  "export_path": "images/output",
  "export_format": "png",
  "resolution_mode": "multiplier",
  "resolution_value": 2,
  "model_name": "eugenesiow/edsr-base"
}
```
