import cv2
from pathlib import Path
import os

def extract_frames(video_path: Path, output_folder: Path, upscale_frames: bool, upscale_output_folder: Path) -> (list, list):
    """
    Extracts frames from a video file and saves them as PNG images.

    Args:
        video_path (Path): The path to the video file.
        output_folder (Path): The directory to save the extracted frames.
        upscale_frames (bool): A flag to indicate whether to upscale the frames.
        upscale_output_folder (Path): The directory to save the upscaled frames.

    Returns:
        A tuple containing two lists:
        - The list of paths to the extracted frame images.
        - The list of paths to the upscaled frame images (if any).
    """
    if not video_path.exists():
        print(f"Error: Video file not found at {video_path}")
        return [], []

    output_folder.mkdir(parents=True, exist_ok=True)
    if upscale_frames:
        upscale_output_folder.mkdir(parents=True, exist_ok=True)

    video_capture = cv2.VideoCapture(str(video_path))
    if not video_capture.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return [], []

    frame_count = 0
    extracted_frame_paths = []

    video_filename = os.path.splitext(os.path.basename(video_path))[0]

    while True:
        success, frame = video_capture.read()
        if not success:
            break

        frame_count += 1
        frame_filename = f"{video_filename}_frame_{frame_count:04d}.png"
        frame_path = output_folder / frame_filename

        cv2.imwrite(str(frame_path), frame)
        extracted_frame_paths.append(frame_path)

    video_capture.release()
    print(f"Successfully extracted {frame_count} frames to {output_folder}")

    return extracted_frame_paths, []
