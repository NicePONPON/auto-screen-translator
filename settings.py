from PyQt6.QtCore import QSettings

DEFAULTS: dict = {
    "source_lang":    "zh-TW",
    "target_lang":    "en",
    "gemini_api_key": "",
    "toolbar_x":      None,
    "toolbar_y":      None,
    "panel_x":        None,
    "panel_y":        None,
    "panel_w":        320,
    "panel_h":        500,
}


class Settings:
    def __init__(self) -> None:
        self._qs = QSettings("AutoScreenTranslator", "AutoScreenTranslator")

    def get(self, key: str):
        default = DEFAULTS.get(key)
        value = self._qs.value(key, default)
        if isinstance(default, int) and default is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key: str, value) -> None:
        self._qs.setValue(key, value)
