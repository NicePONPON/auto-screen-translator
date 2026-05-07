import os
from PyQt6.QtCore import QThread, pyqtSignal

# Maps Google Translate lang codes → EasyOCR language list.
# English is paired with non-Latin scripts to handle mixed content.
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

# Module-level cache: key = sorted tuple of EasyOCR lang codes
_reader_cache: dict = {}


def get_model_dir() -> str:
    """Return (and create) the directory where EasyOCR stores model files."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = os.path.join(appdata, "ocr_translator", "models")
    os.makedirs(path, exist_ok=True)
    return path


def get_easyocr_langs(lang_code: str) -> list[str]:
    return EASYOCR_LANG_MAP.get(lang_code, ["en"])


class OcrWorker(QThread):
    ocr_done   = pyqtSignal(str)  # extracted text (may be empty string)
    ocr_failed = pyqtSignal(str)  # error message

    def __init__(self, image, lang_code: str, parent=None) -> None:
        super().__init__(parent)
        self.image = image      # PIL.Image.Image from ImageGrab
        self.lang_code = lang_code

    def run(self) -> None:
        global _reader_cache
        try:
            import easyocr          # deferred: keeps startup fast; torch loads here
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

            img_array = np.array(self.image)
            results: list[str] = _reader_cache[key].readtext(
                img_array, detail=0, paragraph=True
            )
            self.ocr_done.emit("\n".join(results).strip())
        except Exception as exc:
            self.ocr_failed.emit(str(exc))
