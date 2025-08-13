
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def generate_date_keyboard(lang_code="tr", days=90):
    today = datetime.today()
    keyboard = []

    for i in range(days):
        day = today + timedelta(days=i)
        label = day.strftime("%Y-%m-%d (%a)")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"date_{label}")])

    keyboard.append([InlineKeyboardButton("⬅️ Geri", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)
