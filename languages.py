
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import json, os

LANGUAGES = {
    "tr": "🇹🇷 Türkçe",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
    "de": "🇩🇪 Deutsch"
}

def get_language_keyboard():
    keyboard = [[InlineKeyboardButton(name, callback_data=code)] for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(keyboard)

def load_translations(lang_code):
    base = os.path.join(os.path.dirname(__file__), "utils", "languages")
    path = os.path.join(base, f"{lang_code}.json")
    fallback = os.path.join(base, "en.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(fallback, "r", encoding="utf-8") as f:
            return json.load(f)
