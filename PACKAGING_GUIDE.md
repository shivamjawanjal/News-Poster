# How to Package Desktop App as Executable

This guide explains how to create a standalone `.exe` file for Windows.

## 1. Install PyInstaller

```bash
pip install pyinstaller
```

## 2. Create the Executable

### Option A: Simple (Recommended for First Time)

```bash
pyinstaller --onefile --windowed --name "News Post Generator" desktop_app.py
```

This creates:
- Single `.exe` file in `dist/` folder
- No console window

### Option B: Using Spec File (Advanced)

```bash
pyinstaller desktop_app.spec
```

The spec file includes:
- Proper data file handling
- Icon support
- Optimized settings

## 3. Add an Icon (Optional)

1. Create or find a 256x256 PNG icon
2. Convert to ICO: [Online converter](https://icoconvert.com/)
3. Place `icon.ico` in project root
4. Run:

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name "News Post Generator" desktop_app.py
```

## 4. Find Your Executable

After building, your `.exe` is in:
```
dist/NewsPostGenerator.exe
```

Or with spec file:
```
dist/NewsPostGenerator/NewsPostGenerator.exe
```

## 5. Distribute

### Create an Installer (Windows)

Install NSIS:
```bash
pip install nsis
```

Or download from: https://nsis.sourceforge.io/

Create installer script `installer.nsi`:

```nsis
!include "MUI2.nsh"

Name "News Post Generator"
OutFile "NewsPostGenerator-Setup.exe"
InstallDir "$PROGRAMFILES\NewsPostGenerator"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\NewsPostGenerator.exe"
  CreateDirectory "$SMPROGRAMS\NewsPostGenerator"
  CreateShortCut "$SMPROGRAMS\NewsPostGenerator\News Post Generator.lnk" "$INSTDIR\NewsPostGenerator.exe"
SectionEnd
```

Build with:
```bash
makensis installer.nsi
```

## 6. Troubleshooting

### "Failed to import module"

Add missing modules to spec file:
```python
hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PIL']
```

### Large .exe file

- It's normal (100-200 MB including Python runtime)
- Use `--onedir` to split files

### Antivirus warnings

- PyInstaller executables sometimes trigger false positives
- Sign your executable with a certificate for production

## 7. Deployment

### GitHub Releases
1. Upload `.exe` to GitHub Releases
2. Users can download and run directly

### Installer (Recommended)
1. Create NSIS installer
2. Users run installer
3. App appears in Start Menu

### Portable
- Just distribute the `.exe`
- No installation needed
- Works from USB drive

## 8. Configuration Files

Make sure `.env` is in the same directory as `.exe`:

```
NewsPostGenerator.exe
.env
posts/
processed_news.json
```

Or create a config folder:
```
NewsPostGenerator.exe
config/.env
posts/
```

## Advanced: Code Signing

For production deployment, sign your executable:

```bash
# Generate certificate
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com NewsPostGenerator.exe
```

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)
- [Code Signing Guide](https://www.ssl.com/article/code-signing-tutorial/)

## Tips

✅ Test the `.exe` thoroughly before distribution  
✅ Include a README in the installer  
✅ Version your releases  
✅ Provide uninstaller  
✅ Keep source code secure  

Ready to distribute? 🚀
