# Colab-Image-Upscaler

This project uses the `super-image` library to upscale images. It's designed to be run in a Google Colab environment and utilizes a pre-trained EDSR (Enhanced Deep Residual Networks for Single Image Super-Resolution) model to enhance image resolution.

## Setup and Installation

To run the notebook locally, you'll need to set up the environment as follows:

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

## Usage

The notebook is primarily designed for Google Colab.

1.  **Open in Google Colab:**
    You can open the notebook directly in Google Colab by clicking the "Open in Colab" badge at the top of the notebook file or by navigating to [Google Colab](https://colab.research.google.com/) and opening it from GitHub.

2.  **Run the notebook:**
    Execute the cells in the `notebooks/Upscale_Images_with_Pretrained_super_image_Models.ipynb` notebook. The notebook will guide you through:
    - Installing the required libraries.
    - Downloading a sample image from a URL.
    - Loading the pre-trained model.
    - Upscaling the image and saving the output.
    - Comparing the model's output with a standard bicubic upscaling method.

3.  **Using Your Own Images:**
    To upscale your own images, you can upload them to your Colab environment and modify the `image` variable in the notebook to load your file.
