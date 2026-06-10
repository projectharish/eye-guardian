"""
Main GUI Dashboard for Eye & Posture Health app.
Features real-time status, statistics, tray integration, and camera preview.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import logging
from PIL import Image, ImageTk, ImageDraw
import pystray
from pystray import MenuItem as item
import cv2
import queue

from main_app import EyePostureHealthApp
from config_gui import ConfigGUI

# Use basic logging without file handler to avoid permission issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EyeGuardianGUI:
    def __init__(self, hidden=False):
        self.app = EyePostureHealthApp()
        self.root = tk.Tk()
        self.root.title("Eye Guardian - Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a1a")  # Premium dark mode
        
        # Style
        self.setup_styles()
        
        # Tray Icon
        self.tray_icon = None
        self.setup_tray()
        
        # Build UI
        self.create_widgets()
        
        # Background App Thread
        self.app_thread = None
        self.start_app_thread()
        
        # Update Loop
        self.update_interval = 1000  # 1 second
        self.root.after(self.update_interval, self.refresh_dashboard)
        
        # Handle Window Close
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Analysis/Camera Window state
        self.camera_window = None
        self.is_analyzing = False
        self.gui_queue = queue.Queue()
        self.root.after(100, self.process_gui_queue)
        
        if hidden:
            # Important: we must call withdraw after all setup
            self.root.withdraw()
            # Start tray in thread immediately
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logger.info("Main GUI initialized in hidden mode")
        else:
            logger.info("Main GUI initialized")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom styles for dark mode
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TLabel", background="#1a1a1a", foreground="#e0e0e0", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#ffffff")
        style.configure("Status.TLabel", font=("Segoe UI", 12), foreground="#4caf50")
        style.configure("Card.TFrame", background="#2d2d2d", relief="raised")
        style.configure("StatsValue.TLabel", background="#2d2d2d", font=("Segoe UI", 24, "bold"), foreground="#00bcd4")
        style.configure("StatsLabel.TLabel", background="#2d2d2d", font=("Segoe UI", 9), foreground="#9e9e9e")
        
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("Action.TButton", 
                  background=[('pressed', '#0097a7'), ('active', '#00acc1')],
                  foreground=[('active', '#ffffff')])

    def create_widgets(self):
        # Main Layout
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text="Eye Guardian", style="Header.TLabel").pack(side="left")
        self.status_label = ttk.Label(header_frame, text="● Monitoring Active", style="Status.TLabel")
        self.status_label.pack(side="right")
        
        # Top Cards (Active Status)
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill="x", pady=10)
        
        self.create_status_card(cards_frame, "Distance Status", "optimal", 0)
        self.create_status_card(cards_frame, "Posture Status", "good", 1)
        self.create_status_card(cards_frame, "Eyes Condition", "relaxed", 2)
        
        # Stats Grid
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="both", expand=True, pady=20)
        
        self.stat_cards = {}
        for i, (key, label) in enumerate([
            ("breaks_count", "Breaks Taken"),
            ("blinks_reminded", "Blinks Reminded"),
            ("posture_alerts", "Posture Alerts"),
            ("session_duration", "Session Time")
        ]):
            card = self.create_stat_card(stats_frame, label, "0", i // 2, i % 2)
            self.stat_cards[key] = card
            
        # Control Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        self.pause_btn = ttk.Button(btn_frame, text="Pause Monitoring", style="Action.TButton", command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="Analyze Now (GUI)", style="Action.TButton", command=self.start_manual_analysis).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Settings", style="Action.TButton", command=self.open_settings).pack(side="right", padx=5)

    def create_status_card(self, parent, title, initial_val, column):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=15)
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        parent.columnconfigure(column, weight=1)
        
        ttk.Label(frame, text=title, style="StatsLabel.TLabel").pack(anchor="w")
        val_label = ttk.Label(frame, text=initial_val.upper(), style="TLabel", font=("Segoe UI", 12, "bold"))
        val_label.pack(anchor="w", pady=(5, 0))
        
        # Store label ref for updates
        if not hasattr(self, 'status_card_labels'): self.status_card_labels = {}
        self.status_card_labels[title] = val_label

    def create_stat_card(self, parent, title, initial_val, row, col):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=20)
        frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        parent.columnconfigure(col, weight=1)
        parent.rowconfigure(row, weight=1)
        
        val_label = ttk.Label(frame, text=initial_val, style="StatsValue.TLabel")
        val_label.pack(anchor="center")
        ttk.Label(frame, text=title, style="StatsLabel.TLabel").pack(anchor="center")
        
        return val_label

    def refresh_dashboard(self):
        stats = self.app.get_stats()
        
        # Update Stats Cards
        for key, label in self.stat_cards.items():
            val = stats.get(key, 0)
            if key == "session_duration":
                h = val // 3600
                m = (val % 3600) // 60
                s = val % 60
                val = f"{h:02d}:{m:02d}:{s:02d}"
            label.config(text=str(val))
            
        # Update Status Cards
        if self.status_card_labels:
            last_res = self.app.last_analysis_result
            dist_status = last_res.get('distance_status', 'N/A').upper()
            post_status = last_res.get('posture_status', 'N/A').upper()
            
            self.status_card_labels["Distance Status"].config(
                text=dist_status, 
                foreground="#4caf50" if "OPTIMAL" in dist_status else "#f44336"
            )
            self.status_card_labels["Posture Status"].config(
                text=post_status,
                foreground="#4caf50" if "GOOD" in post_status else "#f44336"
            )
            
        self.root.after(self.update_interval, self.refresh_dashboard)

    def process_gui_queue(self):
        """Process tasks in the queue for thread-safe GUI updates."""
        try:
            while True:
                task = self.gui_queue.get_nowait()
                task()
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(100, self.process_gui_queue)

    def toggle_pause(self):
        is_paused = self.app.toggle_pause()
        self.pause_btn.config(text="Resume Monitoring" if is_paused else "Pause Monitoring")
        self.status_label.config(
            text="● Monitoring Paused" if is_paused else "● Monitoring Active",
            foreground="#f44336" if is_paused else "#4caf50"
        )

    def start_app_thread(self):
        self.app_thread = threading.Thread(target=self.app.run, daemon=True)
        self.app_thread.start()

    def open_settings(self):
        settings = ConfigGUI(self.app)
        settings.run()

    def start_manual_analysis(self):
        """Starts a manual analysis with a live camera preview in a GUI window."""
        if self.is_analyzing:
            return
            
        self.is_analyzing = True
        self.camera_window = tk.Toplevel(self.root)
        self.camera_window.title("Lively Posture & Distance Tracker")
        self.camera_window.geometry("700x650")
        self.camera_window.configure(bg="#1a1a1a")
        self.camera_window.resizable(False, False)
        
        # Header for the analysis window
        header = tk.Frame(self.camera_window, bg="#2d2d2d", pady=10)
        header.pack(fill="x")
        
        tk.Label(header, text="REAL-TIME POSTURE CALIBRATION", 
                 fg="#00bcd4", bg="#2d2d2d", font=("Segoe UI", 14, "bold")).pack()
        
        self.feedback_label = tk.Label(self.camera_window, text="Adjust your position based on the suggestions below.", 
                              fg="#e0e0e0", bg="#1a1a1a", font=("Segoe UI", 11), pady=10)
        self.feedback_label.pack()
        
        video_container = tk.Frame(self.camera_window, bg="black", padx=2, pady=2)
        video_container.pack(pady=5)
        
        self.video_label = tk.Label(video_container, bg="black")
        self.video_label.pack()
        
        # Suggestions display
        self.suggestion_frame = tk.Frame(self.camera_window, bg="#1a1a1a", pady=10)
        self.suggestion_frame.pack(fill="x", padx=20)
        
        self.suggestion_text = tk.Label(self.suggestion_frame, text="✅ Posture looks good!", 
                                       fg="#4caf50", bg="#1a1a1a", font=("Segoe UI", 16, "bold"))
        self.suggestion_text.pack()

        # Calibration button
        ttk.Button(self.camera_window, text="🎯 Set Current as Ideal", style="Action.TButton", 
                   command=self.perform_calibration).pack(pady=5)

        # Close button
        ttk.Button(self.camera_window, text="Stop Tracking", style="Action.TButton", 
                   command=self.camera_window.destroy).pack(pady=5)
        
        # Run analysis thread
        threading.Thread(target=self._run_gui_analysis, daemon=True).start()

    def perform_calibration(self):
        """Triggers the calibration in camera analyzer and saves config."""
        res = self.app.camera_analyzer.calibrate_current_position()
        if 'success' in res:
            # Update app config so it persists
            self.app.config['camera']['reference_face_width'] = res['width']
            self.app.config['posture_analysis']['base_vertical_offset'] = res['v_offset']
            self.app.save_config()
            messagebox.showinfo("Success", "Calibration complete! Current position is now your reference.")
        else:
            messagebox.showerror("Error", f"Calibration failed: {res.get('error', 'Unknown error')}")

    def _run_gui_analysis(self):
        try:
            self.app.camera_analyzer.start_exclusive_mode()
            if not self.app.camera_analyzer.initialize_camera():
                if self.camera_window.winfo_exists():
                    self.camera_window.destroy()
                self.is_analyzing = False
                messagebox.showerror("Error", "Could not access camera.")
                return
            while self.camera_window.winfo_exists():
                result, frame = self.app.camera_analyzer.analyze_frame_with_preview(mirror=True)
                
                if frame is not None:
                    # Convert CV2 frame to PIL for TK
                    # Resize in OpenCV first (much faster than PIL)
                    frame_resized = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    # PIL resize no longer needed as we did it in CV2
                    img_tk = ImageTk.PhotoImage(image=img)
                    
                    # Update GUI via queue
                    def update_img(itk=img_tk):
                        if self.camera_window.winfo_exists():
                            self.video_label.img_tk = itk
                            self.video_label.config(image=itk)
                    self.gui_queue.put(update_img)
                
                # Update suggestions and feedback via queue
                suggestions = result.get('suggestions', [])
                dist_info = f"Distance: {result.get('distance_cm', 'N/A')}cm"
                
                def update_labels(sug=suggestions, dist=dist_info):
                    if not self.camera_window.winfo_exists(): return
                    if sug:
                        self.suggestion_text.config(text=" | ".join(sug), foreground="#ff9800")
                    else:
                        self.suggestion_text.config(text="✅ Posture looks good!", foreground="#4caf50")
                    
                    self.feedback_label.config(text=dist)
                
                self.gui_queue.put(update_labels)
                time.sleep(0.07) # Reduced frequency to save CPU (~14 FPS)                    
            # Update app state with last known good result if window closed
            self.app.last_analysis_result = result
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
        finally:
            self.app.camera_analyzer.stop_exclusive_mode()
            self.app.camera_analyzer.release_camera()
            self.is_analyzing = False

    def setup_tray(self):
        def on_open(icon, item):
            icon.stop()
            self.root.after(0, self.root.deiconify)

        def on_exit(icon, item):
            icon.stop()
            self.app.shutdown()
            self.root.destroy()
            sys.exit(0)

        # Create a simple icon
        icon_image = self.create_tray_icon()
        
        menu = (
            item('Open Dashboard', on_open),
            item('Pause/Resume', lambda icon, item: self.root.after(0, self.toggle_pause)),
            item('Exit', on_exit)
        )
        
        self.tray_icon = pystray.Icon("EyeGuardian", icon_image, "Eye Guardian", menu)

    def create_tray_icon(self):
        width, height = 64, 64
        image = Image.new('RGB', (width, height), '#1a1a1a')
        dc = ImageDraw.Draw(image)
        # Draw a simple eye-like icon
        dc.ellipse([10, 20, 54, 44], fill='#00bcd4') # Sclera/Iris base
        dc.ellipse([25, 25, 39, 39], fill='black')    # Pupil
        return image

    def minimize_to_tray(self):
        self.root.withdraw()
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    import sys
    from main_app import main as cli_main
    
    # Check for hidden flag (used for autostart)
    hidden = "--hidden" in sys.argv
    
    if len(sys.argv) > 1 and not hidden:
        # If arguments provided (and not just --hidden), run CLI mode
        cli_main()
    else:
        # Otherwise run GUI mode
        gui = EyeGuardianGUI(hidden=hidden)
        gui.run()
