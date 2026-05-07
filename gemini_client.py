import io
from PyQt6.QtCore import QThread, pyqtSignal

from languages import LANG_DISPLAY


def _lang_name(code: str) -> str:
    return LANG_DISPLAY.get(code, code)


class GeminiWorker(QThread):
    result_ready = pyqtSignal(str, str)   # original, translation
    failed       = pyqtSignal(str)         # error message

    def __init__(self, image, source_lang: str, target_lang: str,
                 api_key: str, parent=None) -> None:
        super().__init__(parent)
        self.image       = image        # PIL.Image.Image
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key     = api_key

    def run(self) -> None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")

            target_name = _lang_name(self.target_lang)
            prompt = (
                f"Extract all text visible in this image exactly as it appears, "
                f"then translate it to {target_name}.\n"
                f"Reply using exactly this format with no extra commentary:\n"
                f"ORIGINAL: [original text here]\n"
                f"TRANSLATION: [translated text here]"
            )

            # PIL.Image is accepted directly by the google-generativeai SDK
            response = model.generate_content([self.image, prompt])
            self._parse(response.text.strip())

        except Exception as exc:
            self.failed.emit(str(exc))

    def _parse(self, text: str) -> None:
        original_lines: list[str] = []
        translation_lines: list[str] = []
        section = None

        for line in text.splitlines():
            if line.startswith("ORIGINAL:"):
                section = "o"
                val = line[len("ORIGINAL:"):].strip()
                if val:
                    original_lines.append(val)
            elif line.startswith("TRANSLATION:"):
                section = "t"
                val = line[len("TRANSLATION:"):].strip()
                if val:
                    translation_lines.append(val)
            elif section == "o":
                original_lines.append(line)
            elif section == "t":
                translation_lines.append(line)

        original    = "\n".join(original_lines).strip()
        translation = "\n".join(translation_lines).strip()

        if not translation:
            self.failed.emit("Could not parse Gemini response")
            return

        self.result_ready.emit(original or "(no original text)", translation)
