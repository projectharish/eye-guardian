import cv2

def test_camera(index):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Index {index} failed to open.")
        return False
    ret, frame = cap.read()
    if ret:
        print(f"Index {index} successfully read a frame of shape {frame.shape}.")
        cap.release()
        return True
    else:
        print(f"Index {index} opened but failed to read a frame.")
    cap.release()
    return False

for i in range(5):
    test_camera(i)
