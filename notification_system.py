"""
Cross-platform notification system for Windows and Linux.
Supports customizable notification positions and styles.
"""

import platform
import json
import random
from typing import Dict, List
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import platform-specific notification libraries
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    logger.warning("Plyer not available, using fallback notifications")

try:
    import notify2
    NOTIFY2_AVAILABLE = True
except ImportError:
    NOTIFY2_AVAILABLE = False
    logger.warning("notify2 not available")


class NotificationSystem:
    """Cross-platform notification system with customization."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.system = platform.system()
        self.notification_config = config.get('notifications', {})
        
        # Initialize notify2 for Linux
        if self.system == 'Linux' and NOTIFY2_AVAILABLE:
            try:
                notify2.init('Eye & Posture Health')
            except Exception as e:
                logger.warning(f"Failed to initialize notify2: {e}")
    
    def get_notification_position(self, position: str) -> str:
        """Convert position string to platform-specific format."""
        position_map = {
            'top-right': 'top-right',
            'top-left': 'top-left',
            'bottom-right': 'bottom-right',
            'bottom-left': 'bottom-left',
            'center': 'center'
        }
        return position_map.get(position, 'top-right')
    
    def show_notification(self, title: str, message: str, 
                         notification_type: str = 'break_reminder',
                         position: str = None) -> bool:
        """Show a notification with the given title and message."""
        try:
            # Get notification-specific config
            notif_config = self.notification_config.get(notification_type, {})
            
            # Use provided position or config position
            if position is None:
                position = notif_config.get('position', 'top-right')
            
            # Check if notification type is enabled
            if not notif_config.get('enabled', True):
                return False
            
            # Get duration
            duration = notif_config.get('duration_seconds', 5)
            
            # Platform-specific notification
            if self.system == 'Windows':
                return self._show_windows_notification(title, message, duration, position)
            elif self.system == 'Linux':
                return self._show_linux_notification(title, message, duration, position)
            else:
                return self._show_fallback_notification(title, message)
                
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
            return self._show_fallback_notification(title, message)
    
    def _show_windows_notification(self, title: str, message: str, 
                                   duration: int, position: str) -> bool:
        """Show notification on Windows."""
        try:
            if PLYER_AVAILABLE:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='Eye & Posture Health',
                    timeout=duration,
                    toast_notification=True
                )
                return True
            else:
                return self._show_fallback_notification(title, message)
        except Exception as e:
            logger.error(f"Windows notification error: {e}")
            return self._show_fallback_notification(title, message)
    
    def _show_linux_notification(self, title: str, message: str, 
                                 duration: int, position: str) -> bool:
        """Show notification on Linux."""
        try:
            if NOTIFY2_AVAILABLE:
                n = notify2.Notification(title, message)
                n.set_timeout(duration * 1000)  # Convert to milliseconds
                n.set_urgency(notify2.URGENCY_NORMAL)
                n.show()
                return True
            elif PLYER_AVAILABLE:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='Eye & Posture Health',
                    timeout=duration
                )
                return True
            else:
                return self._show_fallback_notification(title, message)
        except Exception as e:
            logger.error(f"Linux notification error: {e}")
            return self._show_fallback_notification(title, message)
    
    def _show_fallback_notification(self, title: str, message: str) -> bool:
        """Fallback notification using print statement."""
        print(f"\n{'='*60}")
        print(f"NOTIFICATION: {title}")
        print(f"{'='*60}")
        print(f"{message}")
        print(f"{'='*60}\n")
        return True
    
    def show_break_notification(self, messages: List[str]) -> bool:
        """Show a break reminder notification."""
        message = random.choice(messages)
        return self.show_notification(
            title="⏰ Break Reminder",
            message=message,
            notification_type='break_reminder'
        )
    
    def show_blink_notification(self, messages: List[str]) -> bool:
        """Show a blink reminder notification."""
        message = random.choice(messages)
        return self.show_notification(
            title="👁️ Blink Reminder",
            message=message,
            notification_type='blink_reminder'
        )
    
    def show_posture_notification(self, messages: List[str]) -> bool:
        """Show a posture reminder notification."""
        message = random.choice(messages)
        return self.show_notification(
            title="🧘 Posture Reminder",
            message=message,
            notification_type='posture_reminder'
        )
    
    def show_distance_notification(self, messages: List[str], 
                                  distance_status: str) -> bool:
        """Show a distance-related notification."""
        if distance_status == 'too_close':
            message = random.choice(messages)
            return self.show_notification(
                title="📏 Distance Alert",
                message=message,
                notification_type='posture_reminder'
            )
        return False
    
    def show_posture_analysis_notification(self, analysis_result: Dict,
                                          good_messages: List[str],
                                          slouch_messages: List[str],
                                          tilt_messages: List[str]) -> bool:
        """Show notification based on posture analysis."""
        posture_status = analysis_result.get('posture_status', 'unknown')
        suggestions = analysis_result.get('suggestions', [])
        suggestion_text = f"\n👉 {', '.join(suggestions)}" if suggestions else ""
        
        if posture_status == 'good' and not suggestions:
            message = random.choice(good_messages)
            return self.show_notification(
                title="✅ Great Posture!",
                message=message,
                notification_type='posture_reminder'
            )
        elif analysis_result.get('slouching') or analysis_result.get('head_tilt_detected') or suggestions:
            if analysis_result.get('slouching'):
                message = random.choice(slouch_messages)
            elif analysis_result.get('head_tilt_detected'):
                message = random.choice(tilt_messages)
            else:
                message = "Improve your posture."
                
            return self.show_notification(
                title="⚠️ Posture Correction",
                message=message + suggestion_text,
                notification_type='posture_reminder'
            )
        
        return False
    
    def show_distance_analysis_notification(self, analysis_result: Dict,
                                          good_messages: List[str],
                                          distance_messages: List[str]) -> bool:
        """Show notification based on distance analysis."""
        distance_status = analysis_result.get('distance_status', 'unknown')
        suggestions = analysis_result.get('suggestions', [])
        # Only include distance related suggestions if we are specifically here for distance
        dist_suggestions = [s for s in suggestions if "Move" in s]
        suggestion_text = f"\n👉 {', '.join(dist_suggestions)}" if dist_suggestions else ""
        
        if distance_status == 'optimal':
            message = random.choice(good_messages)
            return self.show_notification(
                title="✅ Perfect Distance!",
                message=message,
                notification_type='posture_reminder'
            )
        elif distance_status == 'too_close' or dist_suggestions:
            message = random.choice(distance_messages) if distance_status == 'too_close' else "Please adjust your distance."
            return self.show_notification(
                title="📏 Distance Alert",
                message=message + suggestion_text,
                notification_type='posture_reminder'
            )
        
        return False
    
    def test_notification(self) -> bool:
        """Show a test notification."""
        return self.show_notification(
            title="Test Notification",
            message="Eye & Posture Health app is working!",
            notification_type='break_reminder'
        )
