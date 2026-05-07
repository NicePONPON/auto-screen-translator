# Auto Screen Translator

An always-on-top floating Windows tool that captures any region of your screen, runs OCR on it, and displays the translation in a semi-transparent overlay — right next to what you selected.

## Features

- **Capture any screen region** — drag to select, works across multiple monitors
- **Instant overlay** — translation appears above/below/left/right of your selection
- **100+ languages** — 6 favorites in the toolbar, full searchable list behind "Other…"
- **Always on top** — toolbar and overlay float above every other window
- **Draggable** — move both the toolbar and the result overlay anywhere
- **Persistent settings** — language pair and overlay position remembered across sessions

## Download & Install

See [INSTALL.md](INSTALL.md) or go directly to the [latest release](https://github.com/NicePONPON/auto-screen-translator/releases/tag/latest).

## How it works

```
[Capture button] → full-screen selection mask
       ↓
[PIL.ImageGrab]  → screenshot of selected region
       ↓
[EasyOCR]        → extracted text  (runs in background thread)
       ↓
[deep-translator]→ translated text (runs in background thread)
       ↓
[Floating overlay] → result displayed next to the captured region
```

## Tech stack

- **PyQt6** — UI framework
- **EasyOCR** — OCR engine (supports Traditional Chinese, Simplified Chinese, Japanese, Korean, and more)
- **deep-translator** — Google Translate wrapper (free, no API key)
- **Pillow** — screen capture via `ImageGrab`
- **PyInstaller** — Windows packaging

## Build from source

```bat
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt pyinstaller
python build.py
```

Output: `dist\AutoScreenTranslator\AutoScreenTranslator.exe`
