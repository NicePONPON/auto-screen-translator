# Auto Screen Translator — Installation Guide

## Download (recommended)

1. Go to the [Releases page](https://github.com/NicePONPON/auto-screen-translator/releases/tag/latest)
2. Download **AutoScreenTranslator-Windows.zip**
3. Extract the zip to any folder — e.g. `C:\AutoScreenTranslator\`
4. Double-click **AutoScreenTranslator.exe**

No Python installation required.

## First launch

On your very first Capture, EasyOCR downloads ~180 MB of model files in the background.
The translation result will appear once the download completes (30–60 seconds).
After that first download, every launch is instant.

Model cache location: `%APPDATA%\ocr_translator\models`

## Usage

| Control | Action |
|---------|--------|
| Source / Target dropdowns | Choose languages (6 favorites + searchable full list via "Other…") |
| ↑ ↓ ← → buttons | Choose which side of the capture region the overlay appears on |
| **Capture** button | Draw a rectangle on screen to OCR + translate |
| Drag the overlay | Reposition the result box anywhere on screen |
| × button on overlay | Close the result box |
| Drag the toolbar | Move the floating toolbar anywhere on screen |

## Build from source (advanced)

If you want to build the `.exe` yourself on a Windows machine with Python installed:

```bat
rem Install CPU-only PyTorch first (keeps the package ~600 MB instead of ~3 GB)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

rem Install remaining dependencies
pip install -r requirements.txt pyinstaller

rem Build
python build.py

rem Output: dist\AutoScreenTranslator\AutoScreenTranslator.exe
```
