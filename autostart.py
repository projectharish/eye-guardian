"""
Autostart functionality for Windows and Linux.
Windows: Uses the Registry (HKCU\\...\\Run) — works reliably with PyInstaller executables.
Linux: Uses XDG autostart .desktop files.
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

# Windows registry (built-in, only on Windows)
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

# Registry key path for autostart
_REGISTRY_RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
_REGISTRY_VALUE_NAME = 'EyeGuardian'


def _get_exe_path() -> str:
    """Return the correct executable path whether running as a script or a frozen PyInstaller exe."""
    if getattr(sys, 'frozen', False):
        # Running as a compiled PyInstaller executable
        return sys.executable
    else:
        # Running as a Python script; return raw command without extra quotes
        return f'{sys.executable} {os.path.abspath(sys.argv[0])}'


class AutostartManager:
    """Manages autostart across platforms using the most reliable method per OS."""

    def __init__(self, app_name: str = 'EyeGuardian'):
        self.app_name = app_name
        self.system = platform.system()
        self.exe_path = _get_exe_path()

        # Linux paths
        if self.system == 'Linux':
            self.autostart_dir = os.path.expanduser('~/.config/autostart')
            self.autostart_file = os.path.join(self.autostart_dir, f'{app_name}.desktop')
        else:
            self.autostart_dir = None
            self.autostart_file = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Check if autostart is currently enabled."""
        if self.system == 'Windows' and WINREG_AVAILABLE:
            return self._is_enabled_registry()
        elif self.system == 'Linux':
            return os.path.exists(self.autostart_file)
        return False

    def enable(self) -> bool:
        """Enable autostart."""
        try:
            if self.system == 'Windows':
                return self._enable_windows()
            elif self.system == 'Linux':
                return self._enable_linux()
            else:
                logger.warning(f'Autostart not supported on {self.system}')
                return False
        except Exception as e:
            logger.error(f'Error enabling autostart: {e}')
            return False

    def disable(self) -> bool:
        """Disable autostart."""
        try:
            if self.system == 'Windows':
                return self._disable_windows()
            elif self.system == 'Linux':
                return self._disable_linux()
            return True
        except Exception as e:
            logger.error(f'Error disabling autostart: {e}')
            return False

    def toggle(self) -> bool:
        """Toggle autostart on/off."""
        if self.is_enabled():
            return self.disable()
        return self.enable()

    def get_status(self) -> dict:
        """Get current autostart status."""
        return {
            'enabled': self.is_enabled(),
            'system': self.system,
            'exe_path': self.exe_path,
        }

    # ------------------------------------------------------------------
    # Windows — Registry approach (HKCU\...\Run)
    # ------------------------------------------------------------------

    def _is_enabled_registry(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_RUN_KEY)
            try:
                winreg.QueryValueEx(key, _REGISTRY_VALUE_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except OSError:
            return False

    def _enable_windows(self) -> bool:
        """Enable autostart on Windows via Registry."""
        if not WINREG_AVAILABLE:
            logger.error('winreg not available on this Windows system')
            return False
        try:
            # Build the command: for frozen exe add --hidden flag
            if getattr(sys, 'frozen', False):
                cmd = f'"{self.exe_path}" --hidden'
            else:
                # exe_path is already a raw command string; quote it as a whole
                cmd = f'"{self.exe_path}"'


            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _REGISTRY_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, _REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            logger.info(f'Windows autostart enabled via registry: {cmd}')
            return True
        except OSError as e:
            logger.error(f'Registry write failed: {e}, falling back to Startup folder')
            return self._enable_windows_startup_folder()

    def _disable_windows(self) -> bool:
        """Disable autostart on Windows (registry + clean up old Startup folder entry)."""
        disabled = False
        # Remove registry entry
        if WINREG_AVAILABLE:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    _REGISTRY_RUN_KEY,
                    0,
                    winreg.KEY_SET_VALUE
                )
                winreg.DeleteValue(key, _REGISTRY_VALUE_NAME)
                winreg.CloseKey(key)
                disabled = True
                logger.info('Windows autostart disabled (registry entry removed)')
            except (FileNotFoundError, OSError):
                pass

        # Also clean up any old Startup folder .bat file (legacy cleanup)
        startup_dir = os.path.join(
            os.environ.get('APPDATA', ''),
            'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
        )
        bat_file = os.path.join(startup_dir, f'{self.app_name}.bat')
        if os.path.exists(bat_file):
            try:
                os.remove(bat_file)
                logger.info(f'Legacy Startup folder entry removed: {bat_file}')
            except OSError as e:
                logger.warning(f'Could not remove legacy bat file: {e}')

        return disabled or True

    def _enable_windows_startup_folder(self) -> bool:
        """Fallback: create a .bat file in the Windows Startup folder."""
        try:
            startup_dir = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            os.makedirs(startup_dir, exist_ok=True)
            bat_path = os.path.join(startup_dir, f'{self.app_name}.bat')

            if getattr(sys, 'frozen', False):
                # Frozen exe: just launch it with --hidden
                content = f'@echo off\nstart "" "{self.exe_path}" --hidden\n'
            else:
                content = f'@echo off\nstart "" "{sys.executable}" "{os.path.abspath(sys.argv[0])}"\n'

            with open(bat_path, 'w') as f:
                f.write(content)
            logger.info(f'Windows autostart enabled via Startup folder: {bat_path}')
            return True
        except Exception as e:
            logger.error(f'Startup folder fallback also failed: {e}')
            return False

    # ------------------------------------------------------------------
    # Linux — XDG autostart .desktop file
    # ------------------------------------------------------------------

    def _enable_linux(self) -> bool:
        """Enable autostart on Linux via XDG .desktop file."""
        try:
            os.makedirs(self.autostart_dir, exist_ok=True)
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Eye and Posture Health Reminder
Exec={python_exe} {script_path}
Icon=preferences-desktop
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
            with open(self.autostart_file, 'w') as f:
                f.write(desktop_content)
            os.chmod(self.autostart_file, 0o755)
            logger.info(f'Linux autostart enabled: {self.autostart_file}')
            return True
        except Exception as e:
            logger.error(f'Error enabling Linux autostart: {e}')
            return False

    def _disable_linux(self) -> bool:
        if self.autostart_file and os.path.exists(self.autostart_file):
            try:
                os.remove(self.autostart_file)
                logger.info(f'Linux autostart disabled: {self.autostart_file}')
            except OSError as e:
                logger.error(f'Error removing desktop file: {e}')
                return False
        return True


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def setup_autostart(enable: bool = True) -> bool:
    """Setup autostart based on configuration."""
    manager = AutostartManager()
    return manager.enable() if enable else manager.disable()


def main():
    """CLI entry point for managing autostart."""
    import argparse

    parser = argparse.ArgumentParser(description='Manage EyeGuardian autostart')
    parser.add_argument('--enable',  action='store_true', help='Enable autostart')
    parser.add_argument('--disable', action='store_true', help='Disable autostart')
    parser.add_argument('--status',  action='store_true', help='Show autostart status')
    parser.add_argument('--toggle',  action='store_true', help='Toggle autostart')

    args = parser.parse_args()
    manager = AutostartManager()

    if args.status:
        status = manager.get_status()
        print('Autostart Status:')
        for k, v in status.items():
            print(f'  {k}: {v}')
    elif args.enable:
        ok = manager.enable()
        print('Autostart enabled.' if ok else 'Failed to enable autostart.')
    elif args.disable:
        ok = manager.disable()
        print('Autostart disabled.' if ok else 'Failed to disable autostart.')
    elif args.toggle:
        ok = manager.toggle()
        state = 'enabled' if manager.is_enabled() else 'disabled'
        print(f'Autostart {state}.' if ok else 'Failed to toggle autostart.')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
