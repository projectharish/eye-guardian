"""
Autostart functionality for Windows and Linux.
Handles setting up the app to run automatically on system startup.
"""

import os
import sys
import platform
import shutil
import json
import logging

# Use basic logging without file handler to avoid permission issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutostartManager:
    """Manages autostart functionality across platforms."""
    
    def __init__(self, app_name: str = "EyePostureHealth"):
        self.app_name = app_name
        self.system = platform.system()
        self.script_path = os.path.abspath(sys.argv[0])
        
        # Determine autostart paths
        if self.system == 'Windows':
            self.autostart_dir = os.path.join(
                os.environ['APPDATA'], 
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            self.autostart_file = os.path.join(self.autostart_dir, f'{app_name}.bat')
        elif self.system == 'Linux':
            self.autostart_dir = os.path.expanduser('~/.config/autostart')
            self.autostart_file = os.path.join(self.autostart_dir, f'{app_name}.desktop')
        else:
            self.autostart_dir = None
            self.autostart_file = None
            logger.warning(f"Autostart not supported on {self.system}")
    
    def is_enabled(self) -> bool:
        """Check if autostart is currently enabled."""
        if not self.autostart_file:
            return False
        
        return os.path.exists(self.autostart_file)
    
    def enable(self) -> bool:
        """Enable autostart."""
        try:
            if self.system == 'Windows':
                return self._enable_windows()
            elif self.system == 'Linux':
                return self._enable_linux()
            else:
                logger.warning(f"Autostart not supported on {self.system}")
                return False
        except Exception as e:
            logger.error(f"Error enabling autostart: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable autostart."""
        try:
            if not self.autostart_file or not os.path.exists(self.autostart_file):
                return True
            
            os.remove(self.autostart_file)
            logger.info(f"Autostart disabled: {self.autostart_file}")
            return True
        except Exception as e:
            logger.error(f"Error disabling autostart: {e}")
            return False
    
    def _enable_windows(self) -> bool:
        """Enable autostart on Windows."""
        try:
            # Create startup directory if it doesn't exist
            os.makedirs(self.autostart_dir, exist_ok=True)
            
            # Create batch file
            python_exe = sys.executable
            batch_content = f'@echo off\nstart "" "{python_exe}" "{self.script_path}"\n'
            
            with open(self.autostart_file, 'w') as f:
                f.write(batch_content)
            
            logger.info(f"Autostart enabled on Windows: {self.autostart_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling Windows autostart: {e}")
            return False
    
    def _enable_linux(self) -> bool:
        """Enable autostart on Linux."""
        try:
            # Create autostart directory if it doesn't exist
            os.makedirs(self.autostart_dir, exist_ok=True)
            
            # Create .desktop file
            python_exe = sys.executable
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Eye and Posture Health Reminder
Exec={python_exe} {self.script_path}
Icon=preferences-desktop
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
            
            with open(self.autostart_file, 'w') as f:
                f.write(desktop_content)
            
            # Make file executable
            os.chmod(self.autostart_file, 0o755)
            
            logger.info(f"Autostart enabled on Linux: {self.autostart_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling Linux autostart: {e}")
            return False
    
    def toggle(self) -> bool:
        """Toggle autostart on/off."""
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()
    
    def get_status(self) -> dict:
        """Get current autostart status."""
        return {
            'enabled': self.is_enabled(),
            'system': self.system,
            'autostart_file': self.autostart_file,
            'script_path': self.script_path
        }


def setup_autostart(enable: bool = True) -> bool:
    """Setup autostart based on configuration."""
    manager = AutostartManager()
    
    if enable:
        return manager.enable()
    else:
        return manager.disable()


def main():
    """Main entry point for testing autostart."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage autostart for Eye & Posture Health')
    parser.add_argument('--enable', action='store_true', help='Enable autostart')
    parser.add_argument('--disable', action='store_true', help='Disable autostart')
    parser.add_argument('--status', action='store_true', help='Show autostart status')
    parser.add_argument('--toggle', action='store_true', help='Toggle autostart')
    
    args = parser.parse_args()
    
    manager = AutostartManager()
    
    if args.status:
        status = manager.get_status()
        print(f"Autostart Status:")
        print(f"  Enabled: {status['enabled']}")
        print(f"  System: {status['system']}")
        print(f"  Autostart file: {status['autostart_file']}")
        print(f"  Script path: {status['script_path']}")
    elif args.enable:
        if manager.enable():
            print("Autostart enabled successfully")
        else:
            print("Failed to enable autostart")
    elif args.disable:
        if manager.disable():
            print("Autostart disabled successfully")
        else:
            print("Failed to disable autostart")
    elif args.toggle:
        if manager.toggle():
            print(f"Autostart {'enabled' if manager.is_enabled() else 'disabled'} successfully")
        else:
            print("Failed to toggle autostart")
    else:
        print("Please specify an action: --enable, --disable, --status, or --toggle")


if __name__ == '__main__':
    main()
