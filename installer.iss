; Inno Setup Script for EyeGuardian
; Documentation: http://www.jrsoftware.org/ishelp/
; This installer bundles the standalone EyeGuardian.exe which already
; contains Python and all dependencies (via PyInstaller).
; No Python installation is needed on the target machine.

#define MyAppName "EyeGuardian"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Eye & Posture Health"
#define MyAppURL "https://github.com/yourusername/eye-guardian"
#define MyAppExeName "EyeGuardian.exe"

[Setup]
AppId={{E6F3A5B1-4A5D-4B8E-9C2D-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output installer to the dist folder
OutputDir=dist
OutputBaseFilename=EyeGuardianSetup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Require admin for Program Files install
PrivilegesRequired=admin
; Minimum Windows version (Windows 10+)
MinVersion=10.0
; Uninstall info
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Show license/readme if available
; LicenseFile=LICENSE.txt
; InfoBeforeFile=README.md

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start EyeGuardian automatically when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Main executable (contains embedded Python + all dependencies)
Source: "dist\EyeGuardian.exe"; DestDir: "{app}"; Flags: ignoreversion
; Supporting data files
Source: "face_landmarker.task"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Note: config.json is now stored in %APPDATA%\EyeGuardian\ by the app itself

[Registry]
; Autostart entry (only if user selected the task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "EyeGuardian"; ValueData: """{app}\{#MyAppExeName}"" --hidden"; Flags: uninsdeletevalue; Tasks: autostart

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\app.log"
Type: files; Name: "{app}\eye_posture_health.log"
; Clean up user data directory (config and logs)
Type: filesandordirs; Name: "{userappdata}\EyeGuardian"
Type: dirifempty; Name: "{app}"
