# GitHub Actions Build System

This document explains how to use GitHub Actions to automatically build Windows and Linux installers for EyeGuardian.

## Overview

The project includes GitHub Actions workflows that automatically:
- Build standalone executables for Windows and Linux
- Create installers with all dependencies embedded
- Upload build artifacts
- Create releases when tags are pushed

## Workflows

### 1. Windows Build (`build-windows.yml`)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to these branches
- Release creation
- Manual trigger via workflow_dispatch

**Build Process:**
1. Sets up Python 3.10 on Windows
2. Installs all Python dependencies
3. Downloads MediaPipe face landmarker model
4. Converts icon to Windows format
5. Builds standalone EXE with PyInstaller
6. Installs Inno Setup via Chocolatey
7. Creates installer with Inno Setup
8. Uploads artifacts (EXE and installer)
9. Creates GitHub release (if tagged)

**Outputs:**
- `EyeGuardian-Executable` artifact: Standalone EXE
- `EyeGuardian-Installer` artifact: Installer EXE

### 2. Linux Build (`build-linux.yml`)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to these branches
- Release creation
- Manual trigger via workflow_dispatch

**Build Process:**
1. Sets up Python 3.10 on Ubuntu
2. Installs system dependencies (OpenCV, libnotify)
3. Installs Python dependencies
4. Downloads MediaPipe model
5. Builds standalone executable with PyInstaller
6. Creates tarball
7. Uploads artifact
8. Creates GitHub release (if tagged)

**Outputs:**
- `EyeGuardian-Linux` artifact: Compressed tarball

## Usage

### Automatic Builds

Builds run automatically on:
- Every push to main branches
- Every pull request
- Every release creation

### Manual Trigger

To manually trigger a build:

1. Go to the **Actions** tab in your GitHub repository
2. Select **Build Windows Installer** or **Build Linux Package**
3. Click **Run workflow**
4. Select the branch and click **Run workflow** button

### Creating Releases

To create a release with build artifacts:

1. Create and push a tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. The workflow will automatically:
   - Build the executables
   - Attach them to the GitHub release

3. Or create a release via GitHub UI:
   - Go to **Releases** → **Create a new release**
   - Enter tag version and title
   - Publish the release

## Downloading Artifacts

### From Workflow Runs

1. Go to the **Actions** tab
2. Click on the workflow run
3. Scroll down to **Artifacts** section
4. Download the desired artifact

### From Releases

1. Go to the **Releases** tab
2. Click on the release
3. Download the attached files

## Artifact Details

### Windows Artifacts

**EyeGuardian-Executable** (`EyeGuardian.exe`)
- Standalone executable with embedded Python
- No Python installation required
- Size: ~150-200 MB

**EyeGuardian-Installer** (`EyeGuardianSetup.exe`)
- Professional installer with wizard
- Includes the standalone EXE
- Creates desktop shortcut
- Supports autostart option
- Size: ~150-200 MB

### Linux Artifacts

**EyeGuardian-Linux** (`EyeGuardian-Linux.tar.gz`)
- Standalone executable for Linux
- Compressed tarball
- Extract and run: `./EyeGuardian`
- Size: ~150-200 MB (compressed)

## Configuration

### Modifying Build Settings

**Python Version:**
Edit the workflow files:
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'  # Change this
```

**Dependencies:**
Update `requirements.txt` in the repository root.

**Build Settings:**
Edit `EyeGuardian.spec` for PyInstaller settings.

**Installer Settings:**
Edit `installer.iss` for Inno Setup settings.

### Caching

The workflows use pip caching to speed up builds:
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'
    cache: 'pip'  # Caches dependencies
```

## Troubleshooting

### Build Fails on Dependencies

**Issue:** Python dependencies fail to install

**Solution:**
1. Check `requirements.txt` for correct versions
2. Test locally: `pip install -r requirements.txt`
3. Update workflow to use specific versions if needed

### MediaPipe Model Download Fails

**Issue:** `face_landmarker.task` not found

**Solution:**
1. Ensure `download_models.py` is in the repository
2. Check the download URL in the script
3. Manually upload the model to the repository if needed

### Inno Setup Installation Fails

**Issue:** Chocolatey fails to install Inno Setup

**Solution:**
1. The workflow uses Chocolatey package manager
2. If it fails, Inno Setup may need to be installed differently
3. Consider using a pre-built Inno Setup action

### Artifact Upload Fails

**Issue:** Artifacts not uploaded

**Solution:**
1. Check artifact retention settings (default: 30 days)
2. Ensure artifact paths are correct
3. Check GitHub Actions storage limits

## Security

### Secrets

The workflows use:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- No additional secrets required for basic builds

### Permissions

Required repository permissions:
- `actions: write` - For running workflows
- `contents: write` - For creating releases
- `packages: write` - For uploading artifacts (if using packages)

## Best Practices

1. **Test Locally First**: Always test builds locally before pushing
2. **Use Semantic Versioning**: Use version tags like `v1.0.0`
3. **Monitor Build Times**: Keep an eye on build duration
4. **Clean Up Old Artifacts**: Remove old artifacts to save space
5. **Update Dependencies Regularly**: Keep dependencies up to date

## Advanced Usage

### Matrix Builds

To build for multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

### Custom Build Scripts

To use custom build logic:

```yaml
- name: Custom build
  run: |
    ./custom_build_script.sh
```

### Notifications

Add notifications for build status:

```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: 'Build failed!'
      })
```

## Support

For issues with GitHub Actions:
1. Check the Actions tab for detailed logs
2. Review the workflow syntax
3. Consult GitHub Actions documentation
4. Check the troubleshooting section above

## Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Chocolatey Documentation](https://docs.chocolatey.org/)
