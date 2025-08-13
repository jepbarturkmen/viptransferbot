
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def generate_time_keyboard():
    times = [
        "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
        "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"
    ]

    keyboard = []
    row = []
    for i, t in enumerate(times):
        row.append(InlineKeyboardButton(t, callback_data=f"time_{t}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Geri", callback_data="back_to_date")])
    return InlineKeyboardMarkup(keyboard)
