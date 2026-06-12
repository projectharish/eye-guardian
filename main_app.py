"""
Main application for Eye & Posture Health reminder system.
Runs in background and manages notifications and camera analysis.
"""

import json
import time
import threading
import platform
import os
import sys
import logging
from datetime import datetime
from typing import Dict

from notification_system import NotificationSystem
from camera_analyzer import CameraAnalyzer
from health_messages import (
    BREAK_MESSAGES, BLINK_MESSAGES, POSTURE_MESSAGES,
    DISTANCE_MESSAGES, SLOUCHING_MESSAGES, HEAD_TILT_MESSAGES,
    GOOD_POSTURE_MESSAGES, GOOD_DISTANCE_MESSAGES
)


def get_user_data_dir():
    """Get user-writable directory for config and logs."""
    if platform.system() == 'Windows':
        # Use AppData\Roaming on Windows
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'EyeGuardian')
    elif platform.system() == 'Darwin':
        # Use ~/Library/Application Support on macOS
        data_dir = os.path.expanduser('~/Library/Application Support/EyeGuardian')
    else:
        # Use ~/.config/EyeGuardian on Linux
        data_dir = os.path.expanduser('~/.config/EyeGuardian')
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def setup_logging():
    """Setup logging with user-writable directory."""
    data_dir = get_user_data_dir()
    log_file = os.path.join(data_dir, 'eye_posture_health.log')
    
    # Try to create log file in user directory
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    except (PermissionError, OSError) as e:
        # Fallback to temp directory if user directory fails
        import tempfile
        temp_log = os.path.join(tempfile.gettempdir(), 'eye_posture_health.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(temp_log),
                logging.StreamHandler()
            ]
        )
        print(f"Warning: Could not write to {log_file}, using {temp_log} instead")
    
    return logging.getLogger(__name__)


logger = setup_logging()


class EyePostureHealthApp:
    """Main application class for eye and posture health reminders."""
    
    def __init__(self, config_path: str = None):
        # Use user data directory for config if not specified
        if config_path is None:
            data_dir = get_user_data_dir()
            config_path = os.path.join(data_dir, 'config.json')
        
        self.config_path = config_path
        self.config = self.load_config()
        
        # Initialize components
        self.notification_system = NotificationSystem(self.config)
        self.camera_analyzer = CameraAnalyzer(self.config)
        
        # Timer tracking
        self.last_break_time = time.time()
        self.last_blink_time = time.time()
        self.last_posture_time = time.time()
        self.last_camera_check = time.time()
        
        # Session Statistics
        self.stats = {
            "start_time": time.time(),
            "breaks_count": 0,
            "blinks_reminded": 0,
            "posture_alerts": 0,
            "total_checks": 0,
            "last_face_detected": False,
            "last_distance": 0,
            "last_posture_status": "unknown"
        }
        
        # State tracking
        self.running = False
        self.paused = False
        self.camera_enabled = self.config.get('camera', {}).get('enabled', True)
        self.last_analysis_result = {}
        
        logger.info("Eye & Posture Health App initialized")
    
    def load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            # Create default config in user directory
            default_config = self.get_default_config()
            self.save_config_to_path(default_config, self.config_path)
            return default_config
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration with scientifically optimal values."""
        return {
            "notifications": {
                "break_reminder": {
                    "enabled": True,
                    "interval_minutes": 20,
                    "position": "top-right",
                    "duration_seconds": 20  # Optimized for 20-20-20 rule
                },
                "blink_reminder": {
                    "enabled": True,
                    "interval_minutes": 20,
                    "position": "top-right",
                    "duration_seconds": 5
                },
                "posture_reminder": {
                    "enabled": True,
                    "interval_minutes": 20,
                    "position": "top-right",
                    "duration_seconds": 10
                }
            },
            "camera": {
                "enabled": True,
                "check_interval_minutes": 2,
                "optimal_distance_cm": 60,
                "distance_tolerance_cm": 10,
                "camera_index": 0,
                "reference_face_width": 200
            },
            "posture_analysis": {
                "enabled": True,
                "check_interval_minutes": 2,
                "head_tilt_threshold": 12,
                "slouch_threshold": 15,
                "base_vertical_offset": 0
            },
            "general": {
                "autostart": True,
                "minimize_to_tray": True,
                "sound_enabled": True,
                "language": "en"
            }
        }
    
    def save_config(self):
        """Save current configuration to file."""
        self.save_config_to_path(self.config, self.config_path)
    
    def save_config_to_path(self, config: Dict, path: str):
        """Save configuration to a specific path."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Error saving config to {path}: {e}")
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self.load_config()
        self.notification_system = NotificationSystem(self.config)
        self.camera_analyzer = CameraAnalyzer(self.config)
        self.camera_enabled = self.config.get('camera', {}).get('enabled', True)
        logger.info("Configuration reloaded")
    
    def should_show_break_notification(self) -> bool:
        """Check if it's time for a break notification."""
        config = self.config.get('notifications', {}).get('break_reminder', {})
        if not config.get('enabled', True):
            return False
        
        interval = config.get('interval_minutes', 20) * 60  # Convert to seconds
        return (time.time() - self.last_break_time) >= interval
    
    def should_show_blink_notification(self) -> bool:
        """Check if it's time for a blink notification."""
        config = self.config.get('notifications', {}).get('blink_reminder', {})
        if not config.get('enabled', True):
            return False
        
        interval = config.get('interval_minutes', 20) * 60  # Convert to seconds
        return (time.time() - self.last_blink_time) >= interval
    
    def should_show_posture_notification(self) -> bool:
        """Check if it's time for a posture notification."""
        config = self.config.get('notifications', {}).get('posture_reminder', {})
        if not config.get('enabled', True):
            return False
        
        interval = config.get('interval_minutes', 20) * 60  # Convert to seconds
        return (time.time() - self.last_posture_time) >= interval
    
    def should_check_camera(self) -> bool:
        """Check if it's time for camera analysis."""
        if not self.camera_enabled:
            return False
        
        config = self.config.get('camera', {})
        interval = config.get('check_interval_minutes', 10) * 60  # Convert to seconds
        return (time.time() - self.last_camera_check) >= interval
    
    def show_break_notification(self):
        """Show break notification and update timer."""
        if self.notification_system.show_break_notification(BREAK_MESSAGES):
            self.last_break_time = time.time()
            self.stats['breaks_count'] += 1
            logger.info("Break notification shown")
    
    def show_blink_notification(self):
        """Show blink notification and update timer."""
        if self.notification_system.show_blink_notification(BLINK_MESSAGES):
            self.last_blink_time = time.time()
            self.stats['blinks_reminded'] += 1
            logger.info("Blink notification shown")
    
    def show_posture_notification(self):
        """Show posture notification and update timer."""
        if self.notification_system.show_posture_notification(POSTURE_MESSAGES):
            self.last_posture_time = time.time()
            logger.info("Posture notification shown")
    
    def perform_camera_analysis(self):
        """Perform camera analysis for distance and posture."""
        if not self.camera_enabled:
            return
        
        logger.info("Starting camera analysis...")
        
        try:
            # Perform analysis over 3 seconds
            # continuous_analysis will now respect exclusive mode because we updated release_camera
            result = self.camera_analyzer.continuous_analysis(duration_seconds=3)
            
            if 'error' in result:
                logger.warning(f"Camera analysis error: {result['error']}")
                return
            
            logger.info(f"Camera analysis result: {result}")
            
            if result.get('face_detected'):
                self.stats['last_face_detected'] = True
                self.stats['last_distance'] = result.get('distance_cm')
                self.stats['last_posture_status'] = result.get('posture_status')
                
                # Show notifications based on analysis
                if self.notification_system.show_distance_analysis_notification(
                    result, GOOD_DISTANCE_MESSAGES, DISTANCE_MESSAGES
                ):
                    self.stats['posture_alerts'] += 1
                
                if self.notification_system.show_posture_analysis_notification(
                    result, GOOD_POSTURE_MESSAGES, 
                    SLOUCHING_MESSAGES, HEAD_TILT_MESSAGES
                ):
                    self.stats['posture_alerts'] += 1
            else:
                self.stats['last_face_detected'] = False
            
            self.stats['total_checks'] += 1
            self.last_analysis_result = result
            self.last_camera_check = time.time()
            
        except Exception as e:
            logger.error(f"Error during camera analysis: {e}")
    
    def perform_startup_calibration(self):
        """Initial check during startup to prompt user to adjust position."""
        if not self.camera_enabled:
            return
            
        logger.info("Performing startup posture calibration...")
        self.notification_system.show_notification(
            title="📷 Calibration",
            message="Analyzing your initial sitting position...",
            notification_type='posture_reminder'
        )
        
        # Delay shortly so user can position themselves
        time.sleep(2)
        
        result = self.camera_analyzer.get_quick_analysis()
        if 'error' in result:
            self.notification_system.show_notification(
                title="⚠️ Camera Status",
                message="Camera analysis is unavailable or disabled.",
                notification_type='posture_reminder'
            )
            return

        if result.get('face_detected'):
            status = result.get('distance_status')
            dist = result.get('distance_cm')
            
            if status == 'optimal':
                msg = f"Perfect! Distance is optimal ({dist}cm)."
            elif status == 'too_close':
                msg = f"You are sitting too close ({dist}cm). Please sit back to at least 50cm!"
            else:
                msg = f"You are sitting safely far ({dist}cm)."
                
            self.notification_system.show_notification(
                title="🎯 Distance Check",
                message=msg,
                notification_type='posture_reminder'
            )
        else:
            self.notification_system.show_notification(
                title="🤷 Face Not Detected",
                message="Couldn't find your face for initial calibration.",
                notification_type='posture_reminder'
            )
            
    def run_once(self):
        """Run a single check cycle."""
        try:
            # Check and show notifications
            if self.should_show_break_notification():
                self.show_break_notification()
            
            if self.should_show_blink_notification():
                self.show_blink_notification()
            
            if self.should_show_posture_notification():
                self.show_posture_notification()
            
            # Perform camera analysis
            if self.should_check_camera():
                self.perform_camera_analysis()
            
        except Exception as e:
            logger.error(f"Error in run cycle: {e}")
    
    def run(self):
        """Main run loop."""
        logger.info("Starting Eye & Posture Health App...")
        self.running = True
        
        # Show startup notification
        self.notification_system.show_notification(
            title="🚀 Eye & Posture Health",
            message="App is now running in background. Stay healthy!",
            notification_type='break_reminder'
        )
        
        # Perform Startup calibration
        self.perform_startup_calibration()
        
        try:
            while self.running:
                if not self.paused:
                    self.run_once()
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application."""
        logger.info("Shutting down Eye & Posture Health App...")
        self.running = False
        self.camera_analyzer.release_camera(force=True)
        logger.info("Shutdown complete")
    
    def run_in_background(self):
        """Run the app in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
    
    def test_camera(self):
        """Test camera functionality."""
        logger.info("Testing camera...")
        result = self.camera_analyzer.get_quick_analysis()
        logger.info(f"Camera test result: {result}")
        return result
    
    def test_notifications(self):
        """Test notification system."""
        logger.info("Testing notifications...")
        return self.notification_system.test_notification()

    def get_stats(self) -> Dict:
        """Get current session statistics."""
        stats = self.stats.copy()
        stats['session_duration'] = int(time.time() - stats['start_time'])
        return stats

    def toggle_pause(self):
        """Toggle the pause state of the application."""
        self.paused = not self.paused
        logger.info(f"Application {'paused' if self.paused else 'resumed'}")
        return self.paused


def main():
    """Main entry point."""
    app = EyePostureHealthApp()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test-camera':
            result = app.test_camera()
            print(f"Camera test result: {result}")
            return
        
        elif command == 'test-notification':
            result = app.test_notifications()
            print(f"Notification test: {'Success' if result else 'Failed'}")
            return
        
        elif command == 'config':
            # Launch configuration GUI
            from config_gui import ConfigGUI
            gui = ConfigGUI(app)
            gui.run()
            return
    
    # Run main application
    try:
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
