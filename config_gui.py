"""
Configuration GUI for Eye & Posture Health app.
Built with tkinter for cross-platform compatibility.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import logging

# Use basic logging without file handler to avoid permission issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigGUI:
    """Configuration GUI for the app."""
    
    def __init__(self, app):
        self.app = app
        self.root = tk.Tk()
        self.root.title("Eye & Posture Health - Configuration")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_notifications_tab()
        self.create_camera_tab()
        self.create_posture_tab()
        self.create_general_tab()
        
        # Create button frame
        self.create_button_frame()
        
        logger.info("Configuration GUI initialized")
    
    def create_notifications_tab(self):
        """Create notifications configuration tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='🔔 Notifications')
        
        # Scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Break Reminder Section
        self.create_notification_section(
            scrollable_frame, 'break_reminder', 'Break Reminder',
            'Reminds you to take regular breaks from screen time'
        )
        
        # Blink Reminder Section
        self.create_notification_section(
            scrollable_frame, 'blink_reminder', 'Blink Reminder',
            'Reminds you to blink frequently to prevent dry eyes'
        )
        
        # Posture Reminder Section
        self.create_notification_section(
            scrollable_frame, 'posture_reminder', 'Posture Reminder',
            'Reminds you to maintain good posture'
        )
    
    def create_notification_section(self, parent, key, title, description):
        """Create a notification configuration section."""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Description
        desc_label = ttk.Label(frame, text=description, font=('Arial', 9, 'italic'))
        desc_label.pack(anchor='w', pady=(0, 5))
        
        config = self.app.config.get('notifications', {}).get(key, {})
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=config.get('enabled', True))
        setattr(self, f'{key}_enabled', enabled_var)
        
        enabled_check = ttk.Checkbutton(
            frame, text='Enabled', variable=enabled_var
        )
        enabled_check.pack(anchor='w')
        
        # Interval
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(fill='x', pady=5)
        
        ttk.Label(interval_frame, text='Interval (minutes):').pack(side='left')
        
        interval_var = tk.IntVar(value=config.get('interval_minutes', 20))
        setattr(self, f'{key}_interval', interval_var)
        
        interval_spin = ttk.Spinbox(
            interval_frame, from_=1, to=120, textvariable=interval_var, width=10
        )
        interval_spin.pack(side='right')
        
        # Position
        position_frame = ttk.Frame(frame)
        position_frame.pack(fill='x', pady=5)
        
        ttk.Label(position_frame, text='Position:').pack(side='left')
        
        position_var = tk.StringVar(value=config.get('position', 'top-right'))
        setattr(self, f'{key}_position', position_var)
        
        position_combo = ttk.Combobox(
            position_frame, 
            textvariable=position_var,
            values=['top-right', 'top-left', 'bottom-right', 'bottom-left', 'center'],
            state='readonly',
            width=15
        )
        position_combo.pack(side='right')
        
        # Duration
        duration_frame = ttk.Frame(frame)
        duration_frame.pack(fill='x', pady=5)
        
        ttk.Label(duration_frame, text='Duration (seconds):').pack(side='left')
        
        # For break_reminder, default duration is 20. For others, 10.
        default_dur = 20 if key == 'break_reminder' else 10
        duration_var = tk.IntVar(value=config.get('duration_seconds', default_dur))
        setattr(self, f'{key}_duration', duration_var)
        
        duration_spin = ttk.Spinbox(
            duration_frame, from_=1, to=60, textvariable=duration_var, width=10
        )
        duration_spin.pack(side='right')
    
    def create_camera_tab(self):
        """Create camera configuration tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='📷 Camera')
        
        frame = ttk.LabelFrame(tab, text='Camera Settings', padding=20)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        config = self.app.config.get('camera', {})
        
        # Enabled
        enabled_var = tk.BooleanVar(value=config.get('enabled', True))
        self.camera_enabled = enabled_var
        
        ttk.Checkbutton(frame, text='Enable Camera Analysis', variable=enabled_var).pack(anchor='w', pady=5)
        
        # Camera Index
        index_frame = ttk.Frame(frame)
        index_frame.pack(fill='x', pady=5)
        
        ttk.Label(index_frame, text='Camera Index:').pack(side='left')
        
        index_var = tk.IntVar(value=config.get('camera_index', 0))
        self.camera_index = index_var
        
        ttk.Spinbox(index_frame, from_=0, to=10, textvariable=index_var, width=10).pack(side='right')
        
        # Check Interval
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(fill='x', pady=5)
        
        interval_var = tk.IntVar(value=config.get('check_interval_minutes', 2))
        self.camera_interval = interval_var
        
        ttk.Spinbox(interval_frame, from_=1, to=60, textvariable=interval_var, width=10).pack(side='right')
        
        # Optimal Distance
        distance_frame = ttk.Frame(frame)
        distance_frame.pack(fill='x', pady=5)
        
        distance_var = tk.IntVar(value=config.get('optimal_distance_cm', 60))
        self.optimal_distance = distance_var
        
        ttk.Spinbox(distance_frame, from_=30, to=100, textvariable=distance_var, width=10).pack(side='right')
        
        # Distance Tolerance
        tolerance_frame = ttk.Frame(frame)
        tolerance_frame.pack(fill='x', pady=5)
        
        tolerance_var = tk.IntVar(value=config.get('distance_tolerance_cm', 10))
        self.distance_tolerance = tolerance_var
        
        ttk.Spinbox(tolerance_frame, from_=5, to=30, textvariable=tolerance_var, width=10).pack(side='right')
        
        # Test Camera Button
        test_btn = ttk.Button(frame, text='Test Camera', command=self.test_camera)
        test_btn.pack(pady=10)
    
    def create_posture_tab(self):
        """Create posture analysis configuration tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='🧘 Posture Analysis')
        
        frame = ttk.LabelFrame(tab, text='Posture Analysis Settings', padding=20)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        config = self.app.config.get('posture_analysis', {})
        
        # Enabled
        enabled_var = tk.BooleanVar(value=config.get('enabled', True))
        self.posture_enabled = enabled_var
        
        ttk.Checkbutton(frame, text='Enable Posture Analysis', variable=enabled_var).pack(anchor='w', pady=5)
        
        # Check Interval
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(fill='x', pady=5)
        
        interval_var = tk.IntVar(value=config.get('check_interval_minutes', 2))
        self.posture_interval = interval_var
        
        ttk.Spinbox(interval_frame, from_=1, to=60, textvariable=interval_var, width=10).pack(side='right')
        
        # Head Tilt Threshold
        tilt_frame = ttk.Frame(frame)
        tilt_frame.pack(fill='x', pady=5)
        
        tilt_var = tk.IntVar(value=config.get('head_tilt_threshold', 12))
        self.head_tilt_threshold = tilt_var
        
        ttk.Spinbox(tilt_frame, from_=5, to=45, textvariable=tilt_var, width=10).pack(side='right')
        
        # Slouch Threshold
        slouch_frame = ttk.Frame(frame)
        slouch_frame.pack(fill='x', pady=5)
        
        slouch_var = tk.IntVar(value=config.get('slouch_threshold', 15))
        self.slouch_threshold = slouch_var
        
        ttk.Spinbox(slouch_frame, from_=10, to=50, textvariable=slouch_var, width=10).pack(side='right')
    
    def create_general_tab(self):
        """Create general settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='⚙️ General')
        
        frame = ttk.LabelFrame(tab, text='General Settings', padding=20)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        config = self.app.config.get('general', {})
        
        # Autostart
        autostart_var = tk.BooleanVar(value=config.get('autostart', True))
        self.autostart = autostart_var
        
        ttk.Checkbutton(frame, text='Start with System (Autostart)', variable=autostart_var).pack(anchor='w', pady=5)
        
        # Minimize to Tray
        tray_var = tk.BooleanVar(value=config.get('minimize_to_tray', True))
        self.minimize_to_tray = tray_var
        
        ttk.Checkbutton(frame, text='Minimize to System Tray', variable=tray_var).pack(anchor='w', pady=5)
        
        # Sound Enabled
        sound_var = tk.BooleanVar(value=config.get('sound_enabled', True))
        self.sound_enabled = sound_var
        
        ttk.Checkbutton(frame, text='Enable Notification Sounds', variable=sound_var).pack(anchor='w', pady=5)
        
        # Language
        lang_frame = ttk.Frame(frame)
        lang_frame.pack(fill='x', pady=5)
        
        ttk.Label(lang_frame, text='Language:').pack(side='left')
        
        lang_var = tk.StringVar(value=config.get('language', 'en'))
        self.language = lang_var
        
        ttk.Combobox(
            lang_frame, 
            textvariable=lang_var,
            values=['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja'],
            state='readonly',
            width=15
        ).pack(side='right')
    
    def create_button_frame(self):
        """Create button frame at the bottom."""
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=10, pady=10)
        
        # Save button
        save_btn = ttk.Button(frame, text='Save Configuration', command=self.save_config)
        save_btn.pack(side='left', padx=5)
        
        # Apply button
        apply_btn = ttk.Button(frame, text='Apply', command=self.apply_config)
        apply_btn.pack(side='left', padx=5)
        
        # Reset button
        reset_btn = ttk.Button(frame, text='Reset to Defaults', command=self.reset_config)
        reset_btn.pack(side='left', padx=5)
        
        # Test Notification button
        test_btn = ttk.Button(frame, text='Test Notification', command=self.test_notification)
        test_btn.pack(side='right', padx=5)
        
        # Close button
        close_btn = ttk.Button(frame, text='Close', command=self.close)
        close_btn.pack(side='right', padx=5)
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Update config with GUI values
            self.update_config_from_gui()
            
            # Save to file
            self.app.save_config()
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            logger.info("Configuration saved from GUI")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            logger.error(f"Error saving config: {e}")
    
    def apply_config(self):
        """Apply configuration without saving to file."""
        try:
            self.update_config_from_gui()
            self.app.reload_config()
            messagebox.showinfo("Success", "Configuration applied!")
            logger.info("Configuration applied from GUI")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply configuration: {e}")
            logger.error(f"Error applying config: {e}")
    
    def update_config_from_gui(self):
        """Update config dictionary from GUI values."""
        # Notifications
        self.app.config['notifications']['break_reminder']['enabled'] = self.break_reminder_enabled.get()
        self.app.config['notifications']['break_reminder']['interval_minutes'] = self.break_reminder_interval.get()
        self.app.config['notifications']['break_reminder']['position'] = self.break_reminder_position.get()
        self.app.config['notifications']['break_reminder']['duration_seconds'] = self.break_reminder_duration.get()
        
        self.app.config['notifications']['blink_reminder']['enabled'] = self.blink_reminder_enabled.get()
        self.app.config['notifications']['blink_reminder']['interval_minutes'] = self.blink_reminder_interval.get()
        self.app.config['notifications']['blink_reminder']['position'] = self.blink_reminder_position.get()
        self.app.config['notifications']['blink_reminder']['duration_seconds'] = self.blink_reminder_duration.get()
        
        self.app.config['notifications']['posture_reminder']['enabled'] = self.posture_reminder_enabled.get()
        self.app.config['notifications']['posture_reminder']['interval_minutes'] = self.posture_reminder_interval.get()
        self.app.config['notifications']['posture_reminder']['position'] = self.posture_reminder_position.get()
        self.app.config['notifications']['posture_reminder']['duration_seconds'] = self.posture_reminder_duration.get()
        
        # Camera
        self.app.config['camera']['enabled'] = self.camera_enabled.get()
        self.app.config['camera']['camera_index'] = self.camera_index.get()
        self.app.config['camera']['check_interval_minutes'] = self.camera_interval.get()
        self.app.config['camera']['optimal_distance_cm'] = self.optimal_distance.get()
        self.app.config['camera']['distance_tolerance_cm'] = self.distance_tolerance.get()
        
        # Posture
        self.app.config['posture_analysis']['enabled'] = self.posture_enabled.get()
        self.app.config['posture_analysis']['check_interval_minutes'] = self.posture_interval.get()
        self.app.config['posture_analysis']['head_tilt_threshold'] = self.head_tilt_threshold.get()
        self.app.config['posture_analysis']['slouch_threshold'] = self.slouch_threshold.get()
        
        # General
        self.app.config['general']['autostart'] = self.autostart.get()
        self.app.config['general']['minimize_to_tray'] = self.minimize_to_tray.get()
        self.app.config['general']['sound_enabled'] = self.sound_enabled.get()
        self.app.config['general']['language'] = self.language.get()
    
    def reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            self.app.config = self.app.get_default_config()
            self.app.save_config()
            messagebox.showinfo("Success", "Configuration reset to defaults!")
            logger.info("Configuration reset to defaults")
            self.close()
    
    def test_camera(self):
        """Test camera functionality."""
        result = self.app.test_camera()
        
        if 'error' in result:
            messagebox.showerror("Camera Error", f"Camera test failed: {result['error']}")
        else:
            msg = f"Camera test successful!\n\n"
            msg += f"Face detected: {result.get('face_detected', False)}\n"
            msg += f"Distance: {result.get('distance_cm', 'N/A')} cm\n"
            msg += f"Posture status: {result.get('posture_status', 'N/A')}\n"
            msg += f"Head tilt: {result.get('head_tilt', 'N/A')}°"
            messagebox.showinfo("Camera Test", msg)
    
    def test_notification(self):
        """Test notification system."""
        result = self.app.test_notifications()
        if result:
            messagebox.showinfo("Success", "Test notification sent!")
        else:
            messagebox.showerror("Error", "Failed to send test notification")
    
    def close(self):
        """Close the GUI."""
        self.root.destroy()
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Main entry point for GUI."""
    from main_app import EyePostureHealthApp
    app = EyePostureHealthApp()
    gui = ConfigGUI(app)
    gui.run()


if __name__ == '__main__':
    main()
