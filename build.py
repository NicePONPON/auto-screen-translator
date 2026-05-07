"""
Build AutoScreenTranslator.exe using PyInstaller.

Run from the repo root:

    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt pyinstaller
    python build.py

Output: dist/AutoScreenTranslator/AutoScreenTranslator.exe

First-run model download
------------------------
EasyOCR downloads ~180 MB of model files per OCR language on the first Capture.
They are cached at %APPDATA%\\auto_screen_translator\\models.
Subsequent launches load from cache instantly.
"""

import glob
import subprocess
import sys
import os
import site


def find_package_dir(package: str) -> str | None:
    candidates = list(site.getsitepackages())
    user_sp = site.getusersitepackages()
    if user_sp:
        candidates.append(user_sp)
    for sp in candidates:
        path = os.path.join(sp, package)
        if os.path.isdir(path):
            return path
    return None


def collect_runtime_dlls(sep: str) -> list[str]:
    """Bundle the Visual C++ runtime DLLs that python3XX.dll depends on.

    PyInstaller does not include these automatically.  Without them the app
    fails with 'Failed to load Python DLL / cannot find specified module' on
    machines that don't have the VC++ 2015-2022 Redistributable installed.
    """
    extra: list[str] = []
    search_dirs = [
        os.path.dirname(sys.executable),
        os.path.join(os.path.dirname(sys.executable), "DLLs"),
    ]
    # Patterns cover vcruntime140.dll, vcruntime140_1.dll, msvcp140.dll, etc.
    patterns = [
        "vcruntime140*.dll",
        "msvcp140*.dll",
        "concrt140*.dll",
        "ucrtbase.dll",
    ]
    for d in search_dirs:
        for pat in patterns:
            for dll in glob.glob(os.path.join(d, pat)):
                extra += ["--add-binary", f"{dll}{sep}."]
                print(f"  + bundling runtime DLL: {os.path.basename(dll)}")
    return extra


def collect_torch_dlls(sep: str) -> list[str]:
    """Explicitly bundle every DLL inside torch/lib/ (libtorch, libiomp5, etc.)."""
    extra: list[str] = []
    torch_dir = find_package_dir("torch")
    if torch_dir:
        lib_dir = os.path.join(torch_dir, "lib")
        if os.path.isdir(lib_dir):
            for dll in glob.glob(os.path.join(lib_dir, "*.dll")):
                extra += ["--add-binary", f"{dll}{sep}."]
    return extra


def main() -> None:
    sep = ";" if sys.platform == "win32" else ":"

    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--name",     "AutoScreenTranslator",
        "--onedir",
        "--windowed",
        "--noconfirm",
        # Put ALL support files flat next to the .exe (no _internal/ subfolder).
        # This ensures python311.dll and vcruntime140.dll are in the same directory
        # so Windows DLL search finds them correctly on clean installs.
        "--contents-directory", ".",
        "--collect-all", "easyocr",
        "--collect-all", "deep_translator",
        "--collect-all", "PIL",
        "--collect-all", "torch",
        "--collect-all", "torchvision",
        "--collect-all", "cv2",
        "--collect-all", "certifi",
        "--hidden-import", "torch",
        "--hidden-import", "torchvision",
        "--hidden-import", "torch.nn",
        "--hidden-import", "torch.nn.functional",
        "--hidden-import", "cv2",
    ]

    # easyocr package data (config JSON files)
    easyocr_dir = find_package_dir("easyocr")
    if easyocr_dir:
        cmd += ["--add-data", f"{easyocr_dir}{sep}easyocr"]

    # VC++ runtime DLLs — fixes "Failed to load Python DLL" on clean Windows
    cmd += collect_runtime_dlls(sep)

    # torch/lib DLLs — ensures libtorch, libiomp5, etc. are present
    cmd += collect_torch_dlls(sep)

    cmd.append("main.py")

    print("=" * 60)
    print("Building AutoScreenTranslator ...")
    print("=" * 60)
    subprocess.run(cmd, check=True)

    print()
    print("Build complete!")
    print("Executable: dist/AutoScreenTranslator/AutoScreenTranslator.exe")


if __name__ == "__main__":
    main()
