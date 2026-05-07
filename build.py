"""
Build OCRTranslator.exe using PyInstaller.

Run this script from inside the ocr_translator/ directory:

    cd ocr_translator
    pip install pyinstaller
    python build.py

Output: dist/OCRTranslator/OCRTranslator.exe  (--onedir for fast startup)

IMPORTANT — install CPU-only PyTorch before building to keep the
package size manageable (~600 MB vs ~3 GB for GPU):

    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt

First-run model download
------------------------
EasyOCR does NOT bundle model weights in the .exe.  On the first Capture,
the app downloads ~180 MB of model files per OCR language and caches them at:

    %APPDATA%\\ocr_translator\\models

Subsequent runs load from this cache and start instantly.
The download happens inside the background worker thread — the UI stays
responsive during the wait.
"""

import subprocess
import sys
import os
import site


def find_package_dir(package: str) -> str | None:
    """Return the on-disk path of an installed Python package directory."""
    candidates = list(site.getsitepackages())
    user_sp = site.getusersitepackages()
    if user_sp:
        candidates.append(user_sp)
    for sp in candidates:
        path = os.path.join(sp, package)
        if os.path.isdir(path):
            return path
    return None


def main() -> None:
    sep = ";" if sys.platform == "win32" else ":"

    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--name",     "AutoScreenTranslator",
        "--onedir",                       # faster launch than --onefile
        "--windowed",                     # suppress console window
        "--noconfirm",
        # Collect full package trees that static analysis misses
        "--collect-all", "easyocr",
        "--collect-all", "deep_translator",
        "--collect-all", "PIL",
        "--collect-all", "torch",
        "--collect-all", "torchvision",
        "--collect-all", "cv2",
        "--collect-all", "certifi",
        # Explicit hidden imports for torch internals used by EasyOCR
        "--hidden-import", "torch",
        "--hidden-import", "torchvision",
        "--hidden-import", "torch.nn",
        "--hidden-import", "torch.nn.functional",
        "--hidden-import", "cv2",
    ]

    # Include the easyocr package data (config JSON files, etc.)
    easyocr_dir = find_package_dir("easyocr")
    if easyocr_dir:
        cmd += ["--add-data", f"{easyocr_dir}{sep}easyocr"]

    cmd.append("main.py")

    print("=" * 60)
    print("Building OCRTranslator …")
    print("Command:", " ".join(cmd))
    print("=" * 60)

    subprocess.run(cmd, check=True)

    print()
    print("Build complete!")
    print("Executable: dist/AutoScreenTranslator/AutoScreenTranslator.exe")
    print()
    print("First-run note:")
    print("  EasyOCR will download model weights on the first Capture.")
    print("  Cache location: %APPDATA%\\ocr_translator\\models")


if __name__ == "__main__":
    main()
