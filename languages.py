FAVORITES: list[tuple[str, str]] = [
    ("English",              "en"),
    ("Traditional Chinese",  "zh-TW"),
    ("Simplified Chinese",   "zh-CN"),
    ("Japanese",             "ja"),
    ("Korean",               "ko"),
    ("Spanish",              "es"),
]

# Used in Gemini prompt — maps lang code to display name
LANG_DISPLAY: dict[str, str] = {code: name for name, code in FAVORITES}
LANG_DISPLAY.update({
    "fr": "French",   "de": "German",   "it": "Italian",
    "pt": "Portuguese", "ru": "Russian", "ar": "Arabic",
    "th": "Thai",     "vi": "Vietnamese", "hi": "Hindi",
    "nl": "Dutch",    "pl": "Polish",   "sv": "Swedish",
    "tr": "Turkish",  "uk": "Ukrainian", "id": "Indonesian",
})

ALL_LANGUAGES: dict[str, str] = {
    "Afrikaans": "af", "Albanian": "sq", "Arabic": "ar",
    "Armenian": "hy", "Bengali": "bn", "Bosnian": "bs",
    "Bulgarian": "bg", "Catalan": "ca",
    "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "Croatian": "hr", "Czech": "cs", "Danish": "da",
    "Dutch": "nl", "English": "en", "Estonian": "et",
    "Finnish": "fi", "French": "fr", "German": "de",
    "Greek": "el", "Gujarati": "gu", "Hebrew": "he",
    "Hindi": "hi", "Hungarian": "hu", "Indonesian": "id",
    "Italian": "it", "Japanese": "ja", "Kannada": "kn",
    "Korean": "ko", "Latvian": "lv", "Lithuanian": "lt",
    "Malay": "ms", "Malayalam": "ml", "Marathi": "mr",
    "Nepali": "ne", "Norwegian": "no", "Persian": "fa",
    "Polish": "pl", "Portuguese": "pt", "Punjabi": "pa",
    "Romanian": "ro", "Russian": "ru", "Serbian": "sr",
    "Slovak": "sk", "Slovenian": "sl", "Spanish": "es",
    "Swahili": "sw", "Swedish": "sv", "Tamil": "ta",
    "Telugu": "te", "Thai": "th", "Turkish": "tr",
    "Ukrainian": "uk", "Urdu": "ur", "Vietnamese": "vi",
    "Welsh": "cy", "Zulu": "zu",
}


def get_all_languages() -> dict:
    """Return {DisplayName: lang_code} — static list, no network call."""
    return ALL_LANGUAGES
