import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_face_landmarker():
    """Download the MediaPipe face landmarker model."""
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    filename = "face_landmarker.task"
    
    if os.path.exists(filename):
        logger.info(f"Model {filename} already exists.")
        return True
    
    logger.info(f"Downloading MediaPipe model from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False

if __name__ == "__main__":
    download_face_landmarker()
