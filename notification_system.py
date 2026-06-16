"""
Cross-platform notification system for Windows and Linux.
Supports customizable notification positions and styles.
Windows: Uses native toast notifications via PowerShell + permission checks.
Linux: Uses notify2 / plyer with fallback.
"""

import platform
import json
import random
import subprocess
import sys
from typing import Dict, List
import logging
import os

# Use basic logging without file handler to avoid permission issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

# Windows registry module (built-in, only available on Windows)
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

# tkinter reference stored at class level (set by main_gui)
_tk_root_ref = None

def set_tk_root(root):
    """Store a reference to the tkinter root so we can show popup fallbacks."""
    global _tk_root_ref
    _tk_root_ref = root


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
                # Ensure Windows notifications are allowed
                status = self.check_windows_notification_permissions()
                if not status['allowed']:
                    self.prompt_windows_notification_permissions()
                return self._show_windows_notification(title, message, duration, position)
            elif self.system == 'Linux':
                return self._show_linux_notification(title, message, duration, position)
            else:
                return self._show_fallback_notification(title, message)
                
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
            return self._show_fallback_notification(title, message)
    
    def check_windows_notification_permissions(self) -> Dict:
        """Check if Windows notifications are enabled. Returns a dict with status details."""
        if self.system != 'Windows' or not WINREG_AVAILABLE:
            return {'allowed': True, 'reason': 'N/A'}

        issues = []
        try:
            # Check global notification settings
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\PushNotifications'
            )
            try:
                toast_enabled, _ = winreg.QueryValueEx(key, 'ToastEnabled')
                if toast_enabled == 0:
                    issues.append('Windows toast notifications are disabled in system settings.')
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)

            # Check Focus Assist (Do Not Disturb) - Windows 10/11
            try:
                key2 = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\QuietHours'
                )
                profile, _ = winreg.QueryValueEx(key2, 'Profile')
                # 0=off, 1=priority only, 2=alarms only
                if profile and int(profile) > 0:
                    issues.append('Focus Assist (Do Not Disturb) is enabled and may block notifications.')
                winreg.CloseKey(key2)
            except (FileNotFoundError, OSError):
                pass

        except OSError as e:
            logger.debug(f'Could not read notification registry: {e}')

        return {'allowed': len(issues) == 0, 'reason': ' '.join(issues) if issues else 'OK'}

    def prompt_windows_notification_permissions(self):
        """Show a dialog prompting user to enable notifications if they are blocked."""
        if self.system != 'Windows':
            return
        status = self.check_windows_notification_permissions()
        if not status['allowed']:
            import tkinter as tk
            from tkinter import messagebox
            # Use stored tk root or create a temporary one
            root = _tk_root_ref
            if root is None:
                root = tk.Tk()
                root.withdraw()
                temp = True
            else:
                temp = False
            try:
                result = messagebox.askyesno(
                    'EyeGuardian - Notification Permissions',
                    'Windows may be blocking desktop notifications.\n\n'
                    f"Issue detected:\n{status['reason']}\n\n"
                    'Would you like to open Windows Notification Settings now?\n'
                    'Please enable "Get notifications from apps and other senders" '
                    'and turn off Focus Assist / Do Not Disturb.'
                )
                if result:
                    # Open Windows notification settings
                    subprocess.Popen(
                        ['powershell', '-Command',
                         'Start-Process "ms-settings:notifications"'],
                        creationflags=0x08000000  # CREATE_NO_WINDOW
                    )
            finally:
                if temp:
                    root.destroy()

    def _show_windows_notification(self, title: str, message: str,
                                   duration: int, position: str) -> bool:
        """Show notification on Windows using native PowerShell toast, with plyer fallback."""
        shown = False

        # Method 1: Native Windows toast via PowerShell (most reliable, no extra deps)
        try:
            # Escape single quotes in message for PowerShell
            safe_title = title.replace("'", "''")
            safe_message = message.replace("'", "''")
            ps_script = (
                "[Windows.UI.Notifications.ToastNotificationManager, "
                "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
                "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, "
                "ContentType = WindowsRuntime] | Out-Null\n"
                f"$xml = @'\n"
                "<toast duration=\"long\">\n"
                "  <visual>\n"
                "    <binding template=\"ToastGeneric\">\n"
                f"      <text>{safe_title}</text>\n"
                f"      <text>{safe_message}</text>\n"
                "    </binding>\n"
                "  </visual>\n"
                "  <audio src=\"ms-winsoundevent:Notification.Default\"/>\n"
                "</toast>\n"
                "'@\n"
                "$doc = [Windows.Data.Xml.Dom.XmlDocument]::new()\n"
                "$doc.LoadXml($xml)\n"
                "$notifier = [Windows.UI.Notifications.ToastNotificationManager]::"
                "CreateToastNotifier('EyeGuardian')\n"
                "$toast = [Windows.UI.Notifications.ToastNotification]::new($doc)\n"
                "$notifier.Show($toast)\n"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True, text=True, timeout=10,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                shown = True
                logger.info('Windows toast notification sent via PowerShell')
            else:
                logger.warning(f'PowerShell toast failed: {result.stderr.strip()}')
        except Exception as e:
            logger.warning(f'PowerShell toast error: {e}')

        # Method 2: Plyer fallback (balloon-style, older Windows)
        if not shown and PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='EyeGuardian',
                    timeout=duration,
                    toast_notification=True
                )
                shown = True
                logger.info('Plyer toast notification sent')
            except Exception as e:
                logger.warning(f'Plyer notification error: {e}')

        # Method 3: tkinter popup fallback (guaranteed visible)
        if not shown:
            return self._show_tkinter_popup(title, message, duration)

        return True

    def _show_tkinter_popup(self, title: str, message: str, duration: int = 10) -> bool:
        """Show a tkinter popup window as a last-resort fallback. Always visible."""
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = _tk_root_ref
            if root is not None:
                # Schedule on main thread (safe for tkinter)
                root.after(0, lambda: messagebox.showinfo(title, message))
                return True
            else:
                # No root available - create temporary one
                tmp = tk.Tk()
                tmp.withdraw()
                messagebox.showinfo(title, message)
                tmp.destroy()
                return True
        except Exception as e:
            logger.error(f'tkinter popup fallback error: {e}')
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
