
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.state import reset_booking

LANGUAGE_BUTTONS = [("Türkçe","tr"),("English","en"),("Русский","ru"),("Deutsch","de"),("العربية","ar")]

def language_keyboard():
    rows = [[InlineKeyboardButton(text, callback_data=code)] for text, code in LANGUAGE_BUTTONS]
    return InlineKeyboardMarkup(rows)

def main_menu_keyboard(tr):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tr.get("btn_new_booking","🆕 New Booking"), callback_data="new_booking")],
        [InlineKeyboardButton(tr.get("btn_upload_pdf","📎 Upload PDF/Image"), callback_data="upload_pdf")],
        [InlineKeyboardButton(tr.get("btn_contact_dispatcher","📞 Contact Dispatcher"), callback_data="contact_dispatcher")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "tr")
    tr = load_translations(lang)
    if update.message:
        await update.message.reply_text(tr.get("choose_language","Dil seçin:"), reply_markup=language_keyboard())
    else:
        await update.callback_query.message.reply_text(tr.get("choose_language","Dil seçin:"), reply_markup=language_keyboard())

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data  # 'tr' | 'en' | ...
    context.user_data["language"] = lang_code
    tr = load_translations(lang_code)
    await query.message.edit_text(tr.get("main_menu","Main Menu"), reply_markup=main_menu_keyboard(tr))

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # works for both button and fallback
    reset_booking(context.user_data)
    tr = load_translations(context.user_data.get("language", "tr"))
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(tr.get("main_menu","Main Menu"), reply_markup=main_menu_keyboard(tr))
    else:
        await update.message.reply_text(tr.get("main_menu","Main Menu"), reply_markup=main_menu_keyboard(tr))
