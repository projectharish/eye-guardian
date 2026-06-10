# Windows Build Instructions

This document provides instructions for building the Windows installer for EyeGuardian.

## Prerequisites

### Required Software
1. **Python 3.10 or higher** - Download from https://python.org
   - During installation, check "Add Python to PATH"
   
2. **Git** - Download from https://git-scm.com (optional, for cloning)

3. **Inno Setup 6** - Download from https://jrsoftware.org/isdl.php
   - Required for creating the installer
   - Install the Unicode version

### Python Dependencies
All dependencies are listed in `requirements.txt` and will be installed automatically by the build script.

## Build Process

### Option 1: Automated Build (Recommended)

1. **Open Command Prompt as Administrator**
   - Right-click Command Prompt
   - Select "Run as administrator"

2. **Navigate to the project directory**
   ```cmd
   cd "C:\path\to\eye notification app"
   ```

3. **Run the build script**
   ```cmd
   build_windows.bat
   ```

The script will:
- Install all Python dependencies
- Download the MediaPipe face landmarker model
- Convert the icon to Windows format
- Build the standalone executable with PyInstaller
- Create the installer with Inno Setup (if installed)

### Option 2: Manual Build

If you prefer to build manually or the automated script fails:

#### Step 1: Install Dependencies
```cmd
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Download Model
```cmd
python download_models.py
```

#### Step 3: Convert Icon
```cmd
python convert_icon.py
```

#### Step 4: Build Executable
```cmd
pyinstaller --clean EyeGuardian.spec
```

#### Step 5: Create Installer
If Inno Setup is installed:
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Or:
- Right-click `installer.iss`
- Select "Compile"

## Output Files

After successful build, you will find:

- **Standalone Executable**: `dist\EyeGuardian.exe`
  - Contains embedded Python and all dependencies
  - No Python installation required on target machine
  
- **Installer**: `dist\EyeGuardianSetup.exe`
  - Professional installer with wizard
  - Handles installation to Program Files
  - Creates desktop shortcut
  - Supports autostart option

## Testing the Build

### Test the Executable
```cmd
dist\EyeGuardian.exe
```

### Test the Installer
```cmd
dist\EyeGuardianSetup.exe
```

## Troubleshooting

### PyInstaller Build Fails

**Issue**: Missing dependencies or import errors

**Solution**:
```cmd
pip install --upgrade pyinstaller
pip install --upgrade -r requirements.txt
```

### Inno Setup Not Found

**Issue**: Installer creation skipped

**Solution**:
1. Download Inno Setup from https://jrsoftware.org/isdl.php
2. Install it to the default location
3. Re-run the build script

### Model Download Fails

**Issue**: face_landmarker.task not found

**Solution**:
```cmd
python download_models.py
```

If that fails, manually download from:
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

Place it in the project root directory.

### Icon Conversion Fails

**Issue**: icon.ico not created

**Solution**:
Ensure Pillow is installed:
```cmd
pip install Pillow
```

Or use an online converter to create icon.ico from icon.png

### Permission Errors

**Issue**: Cannot write to Program Files during testing

**Solution**:
- Test the executable from a different location (e.g., Desktop)
- The installer handles permissions correctly
- The app now stores config/logs in %APPDATA%\EyeGuardian\

## Distribution

The `dist\EyeGuardianSetup.exe` file is ready for distribution:
- Single file installer
- No dependencies required on target machine
- Works on Windows 10 and later
- Approximately 150-200 MB (due to embedded Python and MediaPipe)

## Version Updates

To update the version number:

1. Edit `installer.iss`:
   ```iss
   #define MyAppVersion "1.0.1"
   ```

2. Rebuild using the build script

## Clean Build

To perform a clean build:

1. Delete the `build` and `dist` directories
2. Run the build script again

```cmd
rmdir /s /q build dist
build_windows.bat
```

## Advanced Options

### Console Mode for Debugging

To see console output (useful for debugging):

Edit `EyeGuardian.spec`:
```python
console=True,  # Change from False to True
```

Then rebuild.

### Reduce File Size

To reduce the executable size (at the cost of compatibility):

Edit `EyeGuardian.spec`:
```python
upx=False,  # Disable UPX compression
```

Or exclude unused packages in the `excludes` list.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the build log output
3. Ensure all prerequisites are installed
4. Verify Python version is 3.10 or higher
