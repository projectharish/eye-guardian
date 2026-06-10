"""
Camera analyzer for face detection, distance calculation, and posture analysis.
Provides highly compatible cross-platform distance tracking using OpenCV Haar cascades.
"""

import cv2
import numpy as np
import time
import logging
from typing import Tuple, Optional, Dict
import os
import sys

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Use basic logging without file handler to avoid permission issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CameraAnalyzer:
    """Analyzes camera feed for distance and slouch detection using MediaPipe or OpenCV fallback."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.camera_index = config.get('camera', {}).get('camera_index', 0)
        self.optimal_distance = config.get('camera', {}).get('optimal_distance_cm', 50)
        self.distance_tolerance = config.get('camera', {}).get('distance_tolerance_cm', 10)
        self.slouch_threshold = config.get('posture_analysis', {}).get('slouch_threshold', 20)
        self.head_tilt_threshold = config.get('posture_analysis', {}).get('head_tilt_threshold', 12)
        
        self.cap = None
        self.face_cascade = None
        self.eye_cascade = None
        self.use_mock = False
        self.mock_start_time = 0
        self._is_exclusive_mode = False  # Flag for GUI live tracking
        
        # MediaPipe variables
        self.landmarker = None
        self.use_mediapipe = MEDIAPIPE_AVAILABLE
        
        # Handle PyInstaller path for model file
        if hasattr(sys, '_MEIPASS'):
            self.model_path = os.path.join(sys._MEIPASS, "face_landmarker.task")
        else:
            self.model_path = "face_landmarker.task"
        
        # Average face width conceptually
        self.AVG_FACE_WIDTH_CM = 14.0
        # Reference width in pixels calibrated approximately at 50cm
        self.reference_face_width = config.get('camera', {}).get('reference_face_width', 200)
        self.base_vertical_offset = config.get('posture_analysis', {}).get('base_vertical_offset', 0)
        
    def initialize_camera(self) -> bool:
        """Initialize camera and analysis engines."""
        try:
            if self.cap and self.cap.isOpened():
                return True
                
            logger.info(f"Opening camera index {self.camera_index}...")
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    logger.error("Could not open hardware camera.")
                    return False
            
            # Try to initialize MediaPipe
            if self.use_mediapipe and os.path.exists(self.model_path):
                try:
                    base_options = python.BaseOptions(model_asset_path=self.model_path)
                    options = vision.FaceLandmarkerOptions(
                        base_options=base_options,
                        running_mode=vision.RunningMode.VIDEO,
                        output_face_blendshapes=False,
                        output_facial_transformation_matrixes=True,
                        num_faces=1)
                    self.landmarker = vision.FaceLandmarker.create_from_options(options)
                    logger.info("MediaPipe Face Landmarker initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize MediaPipe: {e}. Falling back to Haar Cascades.")
                    self.use_mediapipe = False
            else:
                self.use_mediapipe = False
                if MEDIAPIPE_AVAILABLE and not os.path.exists(self.model_path):
                    logger.warning(f"MediaPipe model file {self.model_path} not found. Use download_models.py.")

            # Always load Haar cascades as fallback
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            
            if not self.use_mediapipe and (self.face_cascade.empty() or self.eye_cascade.empty()):
                logger.error("Failed to load Fallback Haar Cascades.")
                return False
                
            logger.info(f"Camera initialized successfully (MediaPipe: {self.use_mediapipe})")
            return True
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def release_camera(self, force: bool = False):
        """Release camera resources unless locked in exclusive mode."""
        if self._is_exclusive_mode and not force:
            logger.debug("Skipping camera release (exclusive mode active)")
            return

        if self.cap:
            self.cap.release()
            self.cap = None

    def start_exclusive_mode(self):
        """Starts exclusive mode for live GUI tracking, preventing background release."""
        self._is_exclusive_mode = True
        logger.info("Camera entered exclusive mode")

    def stop_exclusive_mode(self):
        """Stops exclusive mode, allowing camera to be released."""
        self._is_exclusive_mode = False
        logger.info("Camera exited exclusive mode")
    
    def calculate_distance(self, face_width_pixels: int) -> float:
        """Calculate distance from camera based on face width."""
        if face_width_pixels <= 0:
            return float('inf')
        
        distance_cm = (self.reference_face_width / face_width_pixels) * self.optimal_distance
        return distance_cm

    
    def analyze_frame(self, frame=None) -> Dict:
        """Analyze a single frame and return results."""
        if self.use_mock:
            # ... (mock logic)
            elapsed = time.time() - self.mock_start_time
            cycle = elapsed % 20
            dist = self.optimal_distance
            slouching = False
            result = {
                'face_detected': True,
                'distance_cm': round(dist, 1),
                'slouching': slouching,
                'head_tilt': 0,
                'posture_status': 'poor' if slouching else 'good',
                'suggestions': []
            }
            self._populate_results_from_analysis(result)
            return result
            
        if frame is None:
            if not self.cap or not self.cap.isOpened():
                return {'error': 'Camera not initialized'}
            ret, frame = self.cap.read()
            if not ret:
                return {'error': 'Could not read frame'}
            
        frame_height, frame_width = frame.shape[:2]
        
        # Downscale for faster analysis (e.g., target width 480)
        target_width = 480
        if frame_width > target_width:
            scale = target_width / frame_width
            analysis_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
            a_height, a_width = analysis_frame.shape[:2]
        else:
            analysis_frame = frame
            a_height, a_width = frame_height, frame_width
            scale = 1.0

        result = {
            'face_detected': False,
            'distance_cm': None,
            'slouching': False,
            'posture_status': 'unknown',
            'suggestions': []
        }
        
        try:
            if self.use_mediapipe and self.landmarker:
                # MediaPipe Logic - VIDEO mode requires timestamp
                timestamp_ms = int(time.time() * 1000)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=analysis_frame)
                detection_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
                
                if detection_result.face_landmarks:
                    landmarks = detection_result.face_landmarks[0]
                    result['face_detected'] = True
                    
                    # Calculate Face Width (using landmarks 234 and 454 for outer face)
                    p1 = landmarks[234]
                    p2 = landmarks[454]
                    w_pixels = np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2) * frame_width
                    
                    # Calculate Distance
                    distance = self.calculate_distance(w_pixels)
                    result['distance_cm'] = round(distance, 1)
                    
                    # Head Tilt (using landmarks 33 and 263 for eyes)
                    eye_left = landmarks[33]
                    eye_right = landmarks[263]
                    dy = eye_right.y - eye_left.y
                    dx = eye_right.x - eye_left.x
                    head_tilt = np.degrees(np.arctan2(dy, dx))
                    result['head_tilt'] = round(abs(head_tilt), 1)
                    
                    # Slouching (using nose bridge landmark 168 or nose tip 1)
                    nose_tip = landmarks[1]
                    vertical_offset = (nose_tip.y - 0.5) * 100 - self.base_vertical_offset # Offset from calibrated center
                    result['slouching'] = vertical_offset > self.slouch_threshold
                    
                    # Horizontal centering
                    horizontal_offset = (nose_tip.x - 0.5) * 100
                    if horizontal_offset > 15: result['suggestions'].append("Move Left ⬅️")
                    elif horizontal_offset < -15: result['suggestions'].append("Move Right ➡️")
                    
                    # Calculate Bounding Box for visualization
                    xs = [lm.x for lm in landmarks]
                    ys = [lm.y for lm in landmarks]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)
                    
                    # Store as (x, y, w, h) in pixels
                    result['face_box'] = (
                        int(min_x * frame_width),
                        int(min_y * frame_height),
                        int((max_x - min_x) * frame_width),
                        int((max_y - min_y) * frame_height)
                    )
                    
                    # Populate status and other suggestions
                    self._populate_results_from_analysis(result)
                    return result

            # Fallback to Haar Cascade
            gray = cv2.cvtColor(analysis_frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(int(80 * scale), int(80 * scale))
            )
            
            if len(faces) > 0:
                faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                ax, ay, aw, ah = faces[0]
                
                # Scale back to original frame coordinates for consistent result
                x_pixels, y_pixels, w_pixels, h_pixels = int(ax/scale), int(ay/scale), int(aw/scale), int(ah/scale)
                
                result['face_detected'] = True
                distance = self.calculate_distance(w_pixels)
                result['distance_cm'] = round(distance, 1)
                
                # Check for slouching
                face_center_y = y_pixels + h_pixels / 2
                frame_center_y = frame_height / 2
                vertical_offset = (face_center_y - frame_center_y) / frame_height * 100 - self.base_vertical_offset
                result['slouching'] = vertical_offset > self.slouch_threshold

                # Horizontal centering
                face_center_x = x_pixels + w_pixels / 2
                frame_center_x = frame_width / 2
                horizontal_offset = (face_center_x - frame_center_x) / frame_width * 100
                if horizontal_offset > 15: result['suggestions'].append("Move Right ➡️")
                elif horizontal_offset < -15: result['suggestions'].append("Move Left ⬅️")

                # Head tilt
                roi_gray = gray[y_pixels:y_pixels+h_pixels, x_pixels:x_pixels+w_pixels]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5) # Lowered minNeighbors
                head_tilt = 0
                if len(eyes) >= 2:
                    eyes = sorted(eyes, key=lambda e: e[0])
                    eye1_c = (eyes[0][0] + eyes[0][2]/2, eyes[0][1] + eyes[0][3]/2)
                    eye2_c = (eyes[1][0] + eyes[1][2]/2, eyes[1][1] + eyes[1][3]/2)
                    head_tilt = np.degrees(np.arctan2(eye2_c[1] - eye1_c[1], eye2_c[0] - eye1_c[0]))
                
                result['head_tilt'] = round(abs(head_tilt), 1)
                result['face_box'] = (x_pixels, y_pixels, w_pixels, h_pixels)
                self._populate_results_from_analysis(result)
                    
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            
        return result

    def _populate_results_from_analysis(self, result: Dict):
        """Common logic to fill status and suggestions after analysis."""
        distance = result.get('distance_cm')
        if distance:
            min_dist = self.optimal_distance - self.distance_tolerance
            max_dist = self.optimal_distance + self.distance_tolerance
            if min_dist <= distance <= max_dist:
                result['distance_status'] = 'optimal'
            elif distance < min_dist:
                result['distance_status'] = 'too_close'
                result['suggestions'].append("Move Back ⬆️")
            else:
                result['distance_status'] = 'too_far'
                result['suggestions'].append("Move Closer ⬇️")

        if result.get('slouching'):
            result['suggestions'].append("Sit Up Straight 🧘")
        
        result['head_tilt_detected'] = result.get('head_tilt', 0) > self.head_tilt_threshold
        if result['head_tilt_detected']:
            result['suggestions'].append("Level Your Head ⚖️")
            
        result['posture_status'] = 'poor' if (result.get('slouching') or result['head_tilt_detected']) else 'good'

    def analyze_frame_with_preview(self, mirror: bool = False) -> Tuple[Dict, Optional[np.ndarray]]:
        """Analyze a frame and return both results and the annotated image."""
        if self.use_mock:
            # Create a simple mock frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "DEMO MODE", (200, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            result = self.analyze_frame()
            
            # Simple visualization on mock frame
            color = (0, 255, 0) if result['posture_status'] == 'good' else (0, 0, 255)
            cv2.circle(frame, (320, 240), 50, color, 2)
            cv2.putText(frame, f"Dist: {result['distance_cm']}cm", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            return result, frame

        if not self.cap or not self.cap.isOpened():
            return {'error': 'Camera not initialized'}, None
        
        ret, frame = self.cap.read()
        if not ret:
            return {'error': 'Could not read frame'}, None
            
        frame_height, frame_width = frame.shape[:2]
        
        # Perform analysis using the ALREADY READ frame
        result = self.analyze_frame(frame=frame)
        if 'error' in result:
            if mirror: frame = cv2.flip(frame, 1)
            return result, frame

        try:
            # Mirror frame if requested BEFORE drawing text, so text is readable
            if mirror:
                frame = cv2.flip(frame, 1)

            status_color = (0, 255, 0) if result['posture_status'] == 'good' else (0, 0, 255)
            if result.get('distance_status') == 'too_far':
                status_color = (0, 165, 255)
            
            # 1. Draw Highlights (Bounding Box)
            if 'face_box' in result:
                bx, by, bw, bh = result['face_box']
                if mirror:
                    # Adjust for mirrored display
                    cv2.rectangle(frame, (frame_width - (bx + bw), by), (frame_width - bx, by + bh), status_color, 2)
                else:
                    cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), status_color, 2)
            
            # 2. Draw standard metrics text
            label = f"Dist: {result['distance_cm']}cm ({result.get('distance_status', 'N/A')})"
            cv2.putText(frame, label, (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            posture_label = f"Tilt: {result.get('head_tilt', 0)} deg"
            cv2.putText(frame, posture_label, (20, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Display Suggestions prominently
            if result.get('suggestions'):
                y0, dy = 160, 35
                for i, suggestion in enumerate(result['suggestions']):
                    cv2.putText(frame, suggestion, (20, y0 + i*dy), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            
            if result.get('slouching'):
                cv2.putText(frame, "SLOUCHING!", (frame_width - 150, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            if result.get('head_tilt_detected'):
                cv2.putText(frame, "TILTED!", (frame_width - 150, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    
        except Exception as e:
            logger.error(f"Error drawing on frame: {e}")
            
        return result, frame

    def get_quick_analysis(self) -> Dict:
        if not self.initialize_camera():
            return {'error': 'Could not initialize camera'}
        
        # Warm up
        logger.info("Warming up camera...")
        for i in range(10):
            ret, _ = self.cap.read()
            if not ret:
                logger.warning(f"Warm-up frame {i} failed to read")
            time.sleep(0.05)
        logger.info("Warm-up complete")
        
        result = self.analyze_frame()
        self.release_camera()
        return result
    
    def continuous_analysis(self, duration_seconds: int = 3, callback=None) -> Dict:
        if not self.initialize_camera():
            return {'error': 'Could not initialize camera'}
        
        results = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds:
                result = self.analyze_frame()
                if callback and 'error' not in result:
                    callback(result)
                results.append(result)
                time.sleep(0.1)
        finally:
            self.release_camera()
        
        if not results:
            return {'error': 'No frames analyzed'}
        
        face_detected_count = sum(1 for r in results if r.get('face_detected'))
        if face_detected_count == 0:
            return {'error': 'No face detected'}
        
        distances = [r['distance_cm'] for r in results if r.get('distance_cm')]
        tilts = [r['head_tilt'] for r in results if 'head_tilt' in r]
        slouching_count = sum(1 for r in results if r.get('slouching'))
        tilt_detected_count = sum(1 for r in results if r.get('head_tilt_detected'))
        
        avg_result = {
            'face_detected': True,
            'distance_cm': round(np.mean(distances), 1) if distances else None,
            'head_tilt': round(np.mean(tilts), 1) if tilts else 0,
            'slouching': slouching_count > len(results) / 2,
            'head_tilt_detected': tilt_detected_count > len(results) / 2,
            'samples': len(results)
        }
        
        if avg_result['distance_cm']:
            min_dist = self.optimal_distance - self.distance_tolerance
            max_dist = self.optimal_distance + self.distance_tolerance
            if min_dist <= avg_result['distance_cm'] <= max_dist:
                avg_result['distance_status'] = 'optimal'
            elif avg_result['distance_cm'] < min_dist:
                avg_result['distance_status'] = 'too_close'
            else:
                avg_result['distance_status'] = 'too_far'
                
        avg_result['posture_status'] = 'poor' if avg_result['slouching'] else 'good'
        
        return avg_result

    def calibrate_current_position(self) -> Dict:
        """Sets the current face size and position as the 'optimal' reference."""
        if not self.cap or not self.cap.isOpened():
            if not self.initialize_camera():
                return {'error': 'Could not access camera'}
        
        # Take a few frames to stabilize
        for _ in range(5): self.cap.read()
        ret, frame = self.cap.read()
        if not ret: return {'error': 'Could not read frame'}
        
        frame_height, frame_width = frame.shape[:2]
        
        # Temporary results to extract face width and y position
        if self.use_mediapipe and self.landmarker:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            detection_result = self.landmarker.detect(mp_image)
            if detection_result.face_landmarks:
                landmarks = detection_result.face_landmarks[0]
                p1, p2 = landmarks[234], landmarks[454]
                w_pixels = np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2) * frame_width
                nose_tip = landmarks[1]
                v_offset = (nose_tip.y - 0.5) * 100
                
                self.reference_face_width = w_pixels
                self.base_vertical_offset = v_offset
                return {'success': True, 'width': w_pixels, 'v_offset': v_offset}
        
        # Fallback to Haar
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        if len(faces) > 0:
            x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
            face_center_y = y + h / 2
            v_offset = (face_center_y - (frame_height / 2)) / frame_height * 100
            
            self.reference_face_width = w
            self.base_vertical_offset = v_offset
            return {'success': True, 'width': w, 'v_offset': v_offset}
            
        return {'error': 'No face detected for calibration'}
