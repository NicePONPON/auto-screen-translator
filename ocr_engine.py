import os
from PyQt6.QtCore import QThread, pyqtSignal

EASYOCR_LANG_MAP: dict[str, list[str]] = {
    "en":    ["en"],
    "zh-TW": ["ch_tra", "en"],
    "zh-CN": ["ch_sim", "en"],
    "ja":    ["ja", "en"],
    "ko":    ["ko", "en"],
    "es":    ["es", "en"],
    "fr":    ["fr", "en"],
    "de":    ["de", "en"],
    "it":    ["it", "en"],
    "pt":    ["pt", "en"],
    "ru":    ["ru", "en"],
    "ar":    ["ar"],
    "th":    ["th"],
    "vi":    ["vi", "en"],
    "hi":    ["hi", "en"],
}

# CJK language codes — no spaces between words when joining results
_CJK_LANGS = {"zh-TW", "zh-CN", "ja", "ko"}

# Minimum confidence to include an EasyOCR result (0–1).
# Below this threshold the detected text is usually noise or decorative graphics.
_CONF_THRESHOLD = 0.3

# Upscale images narrower than this before OCR — accuracy drops sharply below ~1000px.
_MIN_OCR_WIDTH = 1200

_reader_cache: dict = {}


def get_model_dir() -> str:
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = os.path.join(appdata, "AutoScreenTranslator", "models")
    os.makedirs(path, exist_ok=True)
    return path


def get_easyocr_langs(lang_code: str) -> list[str]:
    return EASYOCR_LANG_MAP.get(lang_code, ["en"])


def _preprocess(image, lang_code: str):
    """Upscale + sharpen + contrast-boost before OCR for higher accuracy."""
    from PIL import Image, ImageEnhance, ImageFilter

    # Ensure RGB so all PIL ops work
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Upscale small captures — EasyOCR struggles below ~1000px wide
    w, h = image.size
    if w < _MIN_OCR_WIDTH:
        scale = _MIN_OCR_WIDTH / w
        image = image.resize(
            (int(w * scale), int(h * scale)), Image.LANCZOS
        )

    # Boost contrast so text edges are crisp
    image = ImageEnhance.Contrast(image).enhance(1.6)

    # Gentle sharpening to recover detail lost by upscaling
    image = image.filter(ImageFilter.SHARPEN)

    return image


def _join_results(detections: list, lang_code: str) -> str:
    """Filter by confidence, then join with space (Latin) or no separator (CJK)."""
    texts = [
        text.strip()
        for (_, text, conf) in detections
        if conf >= _CONF_THRESHOLD and text.strip()
    ]
    if not texts:
        return ""
    separator = "" if lang_code in _CJK_LANGS else " "
    return separator.join(texts)


class OcrWorker(QThread):
    ocr_done   = pyqtSignal(str)
    ocr_failed = pyqtSignal(str)

    def __init__(self, image, lang_code: str, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.lang_code = lang_code

    def run(self) -> None:
        global _reader_cache
        try:
            import easyocr
            import numpy as np

            langs = get_easyocr_langs(self.lang_code)
            key = tuple(sorted(langs))

            if key not in _reader_cache:
                _reader_cache[key] = easyocr.Reader(
                    langs,
                    model_storage_directory=get_model_dir(),
                    download_enabled=True,
                    verbose=False,
                )

            img = _preprocess(self.image, self.lang_code)
            img_array = np.array(img)

            # detail=1 returns (bbox, text, confidence) — needed for filtering
            detections = _reader_cache[key].readtext(img_array, detail=1, paragraph=False)
            text = _join_results(detections, self.lang_code)
            self.ocr_done.emit(text)
        except Exception as exc:
            self.ocr_failed.emit(str(exc))
