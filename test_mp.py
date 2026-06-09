import sys
import cv2
import mediapipe as mp

def test_camera(index):
    print(f"\n--- Testing Camera Index {index} ---")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Index {index} failed to open.")
    else:
        ret, frame = cap.read()
        if ret:
            print(f"Index {index} SUCCESS: Read frame of shape {frame.shape}")
        else:
            print(f"Index {index} FAILED: Opened but could not read frame.")
        cap.release()

print("MediaPipe version:", mp.__version__)
print("OpenCV version:", cv2.__version__)

for i in range(2):
    test_camera(i)

try:
    print("\n--- Initializing MediaPipe Face Detection ---")
    face_detection = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
    print("MediaPipe Model initialized successfully!")
except Exception as e:
    print(f"MediaPipe Error: {e}")
