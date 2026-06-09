# Eye & Posture Health Reminder App

A comprehensive cross-platform desktop application that helps you maintain healthy screen time habits by reminding you to take breaks, blink frequently, and maintain good posture. The app also uses your webcam to analyze your sitting distance and posture, providing real-time feedback.

## Features

### 🔔 Smart Notifications
- **Break Reminders**: Regular reminders to take breaks from screen time (default: every 20 minutes)
- **Blink Reminders**: Prompts to blink frequently to prevent dry eyes (default: every 5 minutes)
- **Posture Reminders**: Alerts to maintain good posture (default: every 15 minutes)
- **Customizable Position**: Choose where notifications appear on your screen
- **Adjustable Duration**: Control how long notifications stay visible

### 📷 Camera Analysis
- **Distance Detection**: Measures your distance from the screen using face detection
- **Posture Analysis**: Analyzes head tilt and slouching using facial landmarks
- **Real-time Feedback**: Provides suggestions for better positioning
- **Optimal Distance Alerts**: Notifies when you're too close to the screen
- **Posture Corrections**: Alerts when you're slouching or tilting your head

### ⚙️ Customization
- **Configuration GUI**: Easy-to-use interface for all settings
- **Adjustable Intervals**: Customize reminder frequencies
- **Notification Positioning**: Choose where notifications appear
- **Camera Settings**: Configure camera index and analysis parameters
- **Posture Thresholds**: Set sensitivity for posture detection

### 🚀 Cross-Platform
- **Windows Support**: Full support for Windows 10/11
- **Linux Support**: Works on major Linux distributions
- **Autostart**: Automatically starts with your system
- **Background Service**: Runs quietly in the background

## Installation

### Prerequisites
- Python 3.8 or higher
- Webcam (optional, for camera analysis features)
- Administrator privileges (for autostart setup)

### Step 1: Clone or Download
```bash
cd "/home/harish/eye notification app"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install System Dependencies (Linux only)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3-opencv libnotify-bin
```

**Fedora:**
```bash
sudo dnf install python3-opencv libnotify
```

**Arch Linux:**
```bash
sudo pacman -S opencv python-libnotify
```

### Step 4: Install dlib (for advanced face detection)

**Ubuntu/Debian:**
```bash
sudo apt-get install cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

Then install dlib:
```bash
pip install dlib
```

**Note**: If dlib installation fails, the app will fall back to basic face detection using OpenCV Haar cascades.

## Usage

### Running the Application

**Start the main application:**
```bash
python main_app.py
```

**Launch configuration GUI:**
```bash
python main_app.py config
```

**Test camera functionality:**
```bash
python main_app.py test-camera
```

**Test notifications:**
```bash
python main_app.py test-notification
```

### Managing Autostart

**Enable autostart:**
```bash
python autostart.py --enable
```

**Disable autostart:**
```bash
python autostart.py --disable
```

**Check autostart status:**
```bash
python autostart.py --status
```

**Toggle autostart:**
```bash
python autostart.py --toggle
```

## Configuration

### Using the GUI
1. Run `python main_app.py config`
2. Navigate through the tabs:
   - **Notifications**: Configure break, blink, and posture reminders
   - **Camera**: Set camera index, optimal distance, and check intervals
   - **Posture Analysis**: Adjust posture detection thresholds
   - **General**: Configure autostart and other general settings
3. Click "Save Configuration" to persist changes
4. Click "Apply" to test changes without saving

### Manual Configuration
Edit `config.json` directly:

```json
{
  "notifications": {
    "break_reminder": {
      "enabled": true,
      "interval_minutes": 20,
      "position": "top-right",
      "duration_seconds": 10
    },
    "blink_reminder": {
      "enabled": true,
      "interval_minutes": 5,
      "position": "top-right",
      "duration_seconds": 5
    },
    "posture_reminder": {
      "enabled": true,
      "interval_minutes": 15,
      "position": "top-right",
      "duration_seconds": 8
    }
  },
  "camera": {
    "enabled": true,
    "check_interval_minutes": 10,
    "optimal_distance_cm": 50,
    "distance_tolerance_cm": 10,
    "camera_index": 0
  },
  "posture_analysis": {
    "enabled": true,
    "check_interval_minutes": 10,
    "head_tilt_threshold": 15,
    "slouch_threshold": 20
  },
  "general": {
    "autostart": true,
    "minimize_to_tray": true,
    "sound_enabled": true,
    "language": "en"
  }
}
```

## Health Messages

The app includes researched-based health messages for:

- **Break Reminders**: 15 different messages encouraging regular breaks
- **Blink Reminders**: 15 messages about the importance of blinking
- **Posture Reminders**: 15 messages about maintaining good posture
- **Distance Alerts**: 10 messages when you're too close to the screen
- **Slouching Alerts**: 10 messages when slouching is detected
- **Head Tilt Alerts**: 10 messages for head position correction
- **Positive Feedback**: 10 encouraging messages when posture is good

## How It Works

### Distance Calculation
The app uses face detection to calculate your distance from the screen:
1. Detects your face using the webcam
2. Measures the width of your face in pixels
3. Uses the known average face width (14cm) to calculate distance
4. Compares to the optimal distance (default: 50cm)

### Posture Analysis
Using facial landmarks, the app detects:
- **Head Tilt**: Measures the angle of your head relative to your shoulders
- **Slouching**: Detects if your head position is too low in the frame
- **Overall Posture**: Combines multiple factors for comprehensive analysis

### Notification System
- Cross-platform support (Windows and Linux)
- Customizable positions (top-left, top-right, bottom-left, bottom-right, center)
- Adjustable duration
- Platform-specific native notifications

## Troubleshooting

### Camera Not Working
1. Check if your camera is properly connected
2. Verify camera index in configuration (try 0, 1, 2)
3. Ensure no other application is using the camera
4. Test with `python main_app.py test-camera`

### Notifications Not Showing
**Windows:**
- Check if notifications are enabled in Windows Settings
- Verify the app has permission to show notifications

**Linux:**
- Install libnotify-bin: `sudo apt-get install libnotify-bin`
- Check if your desktop environment supports notifications
- Test with `python main_app.py test-notification`

### dlib Installation Fails
- The app will work without dlib using basic face detection
- For advanced features, ensure you have the required system dependencies
- Consider using a pre-compiled dlib wheel for your platform

### Autostart Not Working
**Windows:**
- Run the app as administrator when enabling autostart
- Check the Startup folder in Windows Settings

**Linux:**
- Ensure ~/.config/autostart directory exists
- Check file permissions on the .desktop file
- Verify your desktop environment supports autostart

## Privacy

- The app processes camera data locally on your machine
- No data is sent to external servers
- Camera analysis is performed in real-time and not stored
- You can disable camera features in the configuration

## System Requirements

### Minimum
- Python 3.8+
- 2GB RAM
- Webcam (optional)
- 50MB disk space

### Recommended
- Python 3.10+
- 4GB RAM
- HD Webcam
- 100MB disk space

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For issues, questions, or suggestions, please check the troubleshooting section or create an issue in the project repository.

## Health Tips

Based on research from optometry and ergonomics:

1. **20-20-20 Rule**: Every 20 minutes, look at something 20 feet away for 20 seconds
2. **Blink Frequently**: Normal blink rate is 15-20 times per minute; staring reduces this by 66%
3. **Optimal Distance**: Keep screen 50-70cm (arm's length) from your eyes
4. **Screen Position**: Monitor should be at eye level, slightly below
5. **Regular Breaks**: Take a 2-minute break every 20-30 minutes
6. **Posture**: Keep ears aligned with shoulders, feet flat on floor
7. **Lighting**: Ensure adequate lighting to reduce eye strain
8. **Hydration**: Drink water regularly to maintain overall health

## Acknowledgments

- OpenCV for computer vision
- face_recognition library for advanced face detection
- plyer for cross-platform notifications
- Health recommendations based on optometry and ergonomics research
