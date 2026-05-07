import os
import asyncio
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal

# Maps our lang codes to Windows OCR BCP-47 language tags
WIN_LANG_MAP: dict[str, str] = {
    "en":    "en",
    "zh-TW": "zh-Hant",
    "zh-CN": "zh-Hans",
    "ja":    "ja",
    "ko":    "ko",
    "es":    "es",
    "fr":    "fr",
    "de":    "de",
    "it":    "it",
    "pt":    "pt",
    "ru":    "ru",
    "ar":    "ar",
    "th":    "th",
    "vi":    "vi",
    "hi":    "hi",
    "nl":    "nl",
    "pl":    "pl",
    "sv":    "sv",
    "tr":    "tr",
    "uk":    "uk",
    "id":    "id",
}

_TARGET_WIDTH = 2400  # Windows OCR accuracy increases significantly above ~2000px


def _preprocess(image):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import numpy as np

    # Flatten transparency onto white background
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Upscale aggressively — Windows OCR is resolution-sensitive
    w, h = image.size
    if w < _TARGET_WIDTH:
        scale = _TARGET_WIDTH / w
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Work in grayscale from here
    gray = image.convert("L")
    arr = np.array(gray)

    # Invert light-on-dark text so OCR always sees dark text on white
    if arr.mean() < 127:
        gray = ImageOps.invert(gray)

    # Normalize contrast across the whole image
    gray = ImageOps.autocontrast(gray, cutoff=1)

    # Strong contrast boost
    gray = ImageEnhance.Contrast(gray).enhance(2.5)

    # Unsharp mask sharpens edges better than a simple sharpen filter
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=250, threshold=2))

    # Pad by 30px white border — prevents edge characters being clipped by OCR
    padded = Image.new("L", (gray.width + 60, gray.height + 60), 255)
    padded.paste(gray, (30, 30))

    return padded.convert("RGB")


async def _win_ocr_async(image_path: str, lang_tag: str) -> str:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.globalization import Language
    from winsdk.windows.storage import StorageFile
    from winsdk.windows.graphics.imaging import BitmapDecoder

    lang = Language(lang_tag)
    if not OcrEngine.is_language_supported(lang):
        lang = Language("en")

    engine = OcrEngine.try_create_from_language(lang)
    if engine is None:
        return ""

    file = await StorageFile.get_file_from_path_async(image_path)
    stream = await file.open_async(0)  # FileAccessMode.Read = 0
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    lines = [line.text for line in result.lines]
    return " ".join(lines).strip()


def _run_win_ocr(image, lang_code: str) -> str:
    lang_tag = WIN_LANG_MAP.get(lang_code, "en")
    img = _preprocess(image)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    try:
        img.save(tmp_path, format="PNG")
        # StorageFile.get_file_from_path_async needs an absolute Windows path
        abs_path = os.path.abspath(tmp_path)
        return asyncio.run(_win_ocr_async(abs_path, lang_tag))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


class OcrWorker(QThread):
    ocr_done   = pyqtSignal(str)
    ocr_failed = pyqtSignal(str)

    def __init__(self, image, lang_code: str, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.lang_code = lang_code

    def run(self) -> None:
        try:
            text = _run_win_ocr(self.image, self.lang_code)
            self.ocr_done.emit(text)
        except Exception as exc:
            self.ocr_failed.emit(str(exc))
