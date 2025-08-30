import os
import shutil
import cv2
import ffmpeg
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from PIL import Image

# Helper function to load the FILM model
def load_film_model():
    """Loads the FILM model from TensorFlow Hub."""
    print("Loading FILM model for frame interpolation...")
    model_url = "https://tfhub.dev/google/film/1"
    model = hub.load(model_url)
    print("FILM model loaded successfully.")
    return model

film_model = load_film_model()

def get_video_metadata(video_path):
    """Gets video metadata using OpenCV."""
    video_capture = cv2.VideoCapture(str(video_path))
    if not video_capture.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return None, None
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    resolution = (int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    video_capture.release()
    return fps, resolution

def extract_frames(video_path, temp_dir):
    """Extracts frames from a video file using ffmpeg-python."""
    print(f"Extracting frames from {video_path.name}...")
    try:
        (
            ffmpeg
            .input(str(video_path))
            .output(os.path.join(temp_dir, 'frame-%06d.png'), start_number=0)
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error during frame extraction:")
        print(e.stderr.decode())
        return False
    print("Frame extraction complete.")
    return True

def _load_image_for_film(image_path):
    """Loads an image and prepares it for the FILM model."""
    image = tf.io.read_file(image_path)
    image = tf.io.decode_image(image, channels=3)
    image_numpy = tf.cast(image, dtype=tf.float32).numpy()
    return image_numpy / 255.0

def interpolate_frames(frame1_path, frame2_path):
    """Interpolates a frame between two existing frames using the FILM model."""
    frame1 = _load_image_for_film(frame1_path)
    frame2 = _load_image_for_film(frame2_path)

    # The FILM model expects a batch dimension
    inputs = {
        'x0': tf.expand_dims(frame1, axis=0),
        'x1': tf.expand_dims(frame2, axis=0),
        'time': tf.constant([0.5], dtype=tf.float32) # Interpolate at the midpoint
    }
    
    result = film_model(inputs)
    interpolated_image_tensor = result['image']
    
    # Convert tensor to a PIL image
    interpolated_image_numpy = interpolated_image_tensor.numpy().squeeze()
    interpolated_image = Image.fromarray((interpolated_image_numpy * 255).astype(np.uint8))
    
    return interpolated_image

def encode_video(frames_dir, output_path, original_video_path, config):
    """Encodes a sequence of frames into a video file with audio."""
    print("Encoding upscaled video...")
    video_settings = config.get('video_settings', {})
    codec = video_settings.get('codec', 'h264')
    target_fps = video_settings.get('frame_rate', 0)

    original_fps, _ = get_video_metadata(original_video_path)
    if not original_fps:
        return False
        
    if target_fps <= 0:
        target_fps = original_fps

    try:
        input_video_stream = ffmpeg.input(os.path.join(frames_dir, 'frame-%06d.png'), framerate=target_fps)
        input_audio_stream = ffmpeg.input(str(original_video_path)).audio

        (
            ffmpeg
            .output(input_video_stream, input_audio_stream, str(output_path), vcodec=codec, pix_fmt='yuv420p')
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error during video encoding:")
        print(e.stderr.decode())
        return False

    print(f"Successfully encoded video to: {output_path}")
    return True

def process_video(video_path, config, image_upscaler_model):
    """
    Main function to handle the video upscaling process.
    Orchestrates frame extraction, upscaling, optional interpolation, and re-encoding.
    """
    from upscaler import upscale_image # Import here to avoid circular dependency issues

    print(f"\nStarting video processing for: {video_path.name}")
    
    # Create a unique temporary directory for frames
    temp_dir_name = f"temp_{video_path.stem}_{os.urandom(4).hex()}"
    temp_dir = Path('images/temp') / temp_dir_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract frames from the video
    if not extract_frames(video_path, temp_dir):
        shutil.rmtree(temp_dir)
        return

    # 2. Upscale each frame
    extracted_frames = sorted(list(temp_dir.glob('*.png')))
    upscaled_frames_dir = temp_dir / 'upscaled'
    upscaled_frames_dir.mkdir(exist_ok=True)
    
    for frame_path in extracted_frames:
        # We need to create a slightly modified config for the upscaler
        upscale_config = config.copy()
        upscale_config['export_path'] = str(upscaled_frames_dir)
        upscale_image(frame_path, image_upscaler_model, upscale_config)

    # 3. Optional: Frame Interpolation
    video_settings = config.get('video_settings', {})
    target_fps = video_settings.get('frame_rate', 0)
    original_fps, _ = get_video_metadata(video_path)

    frames_to_encode_dir = upscaled_frames_dir
    if target_fps > original_fps:
        print(f"Interpolating frames to increase framerate from {original_fps:.2f} to {target_fps}...")
        interpolated_frames_dir = temp_dir / 'interpolated'
        interpolated_frames_dir.mkdir(exist_ok=True)
        
        upscaled_frames = sorted(list(upscaled_frames_dir.glob('*.png')))
        
        # This is a simplified interpolation logic. A more robust implementation
        # would be needed for arbitrary frame rate conversion.
        # This will roughly double the framerate.
        frame_counter = 0
        for i in range(len(upscaled_frames) - 1):
            # Save the original frame
            shutil.copy(upscaled_frames[i], interpolated_frames_dir / f"frame-{frame_counter:06d}.png")
            frame_counter += 1
            
            # Create and save the interpolated frame
            interpolated_image = interpolate_frames(str(upscaled_frames[i]), str(upscaled_frames[i+1]))
            interpolated_image.save(interpolated_frames_dir / f"frame-{frame_counter:06d}.png")
            frame_counter += 1
            
        # Save the last frame
        shutil.copy(upscaled_frames[-1], interpolated_frames_dir / f"frame-{frame_counter:06d}.png")
        
        frames_to_encode_dir = interpolated_frames_dir
        print("Frame interpolation complete.")

    # 4. Encode the video
    export_path = Path(config.get('export_path', 'images/output'))
    export_path.mkdir(parents=True, exist_ok=True)
    output_video_path = export_path / f"{video_path.stem}_upscaled.mp4"
    
    encode_video(frames_to_encode_dir, output_video_path, video_path, config)

    # 5. Cleanup
    if not video_settings.get('keep_temp_files', False):
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        print("Cleanup complete.")
    else:
        print(f"Temporary files kept at: {temp_dir}")
