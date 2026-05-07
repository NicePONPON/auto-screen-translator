from PyQt6.QtCore import QThread, pyqtSignal


class TranslatorWorker(QThread):
    translation_ready = pyqtSignal(str, bool)  # (text, success)

    def __init__(self, text: str, source: str, target: str, parent=None) -> None:
        super().__init__(parent)
        self.text   = text
        self.source = source
        self.target = target

    def run(self) -> None:
        try:
            from deep_translator import GoogleTranslator
            result = GoogleTranslator(
                source=self.source, target=self.target
            ).translate(self.text)
            self.translation_ready.emit(result or self.text, True)
        except Exception as exc:
            self.translation_ready.emit(self.text, False)
