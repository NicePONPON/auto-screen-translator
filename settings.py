from PyQt6.QtCore import QSettings

DEFAULTS: dict = {
    "source_lang": "zh-TW",
    "target_lang": "en",
    "overlay_position": "bottom",
    "overlay_opacity": 0.85,
}


class Settings:
    def __init__(self) -> None:
        self._qs = QSettings("OCRTranslator", "OCRTranslator")

    def get(self, key: str):
        default = DEFAULTS.get(key)
        value = self._qs.value(key, default)
        # QSettings may return string even for float values
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key: str, value) -> None:
        self._qs.setValue(key, value)
