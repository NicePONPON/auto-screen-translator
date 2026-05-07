from PyQt6.QtCore import QThread, pyqtSignal
from deep_translator import GoogleTranslator

FAVORITES: list[tuple[str, str]] = [
    ("English", "en"),
    ("Traditional Chinese", "zh-TW"),
    ("Simplified Chinese", "zh-CN"),
    ("Japanese", "ja"),
    ("Korean", "ko"),
    ("Spanish", "es"),
]

_ALL_LANGUAGES_CACHE: dict | None = None


def get_all_languages() -> dict:
    """Return {DisplayName: lang_code} for every Google-supported language.

    Result is cached so the network call happens at most once per process.
    Falls back to FAVORITES on network failure.
    """
    global _ALL_LANGUAGES_CACHE
    if _ALL_LANGUAGES_CACHE is None:
        try:
            raw: dict = GoogleTranslator().get_supported_languages(as_dict=True)
            # raw keys are lowercase display names; values are lang codes
            _ALL_LANGUAGES_CACHE = {name.title(): code for name, code in raw.items()}
        except Exception:
            _ALL_LANGUAGES_CACHE = {name: code for name, code in FAVORITES}
    return _ALL_LANGUAGES_CACHE


class TranslatorWorker(QThread):
    translation_ready = pyqtSignal(str, bool)  # (translated_text, success)

    def __init__(self, text: str, source: str, target: str, parent=None) -> None:
        super().__init__(parent)
        self.text = text
        self.source = source
        self.target = target

    def run(self) -> None:
        try:
            result: str | None = GoogleTranslator(
                source=self.source, target=self.target
            ).translate(self.text)
            self.translation_ready.emit(result or self.text, True)
        except Exception:
            self.translation_ready.emit(self.text, False)
