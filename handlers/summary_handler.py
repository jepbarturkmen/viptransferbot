
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from languages import load_translations

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "tr")
    text = load_translations(lang)

    summary = f"""
📋 <b>{text['summary']}</b>

👤 <b>{text['name']}:</b> {context.user_data.get('name')}
📞 <b>{text['phone']}:</b> {context.user_data.get('phone')}

🚖 <b>{text['from']}:</b> {context.user_data.get('pickup_location')}
📍 <b>{text['to']}:</b> {context.user_data.get('dropoff_location')}
👥 <b>{text['passenger_count']}:</b> {context.user_data.get('passenger_count')}
👶 <b>{text['baby_seat']}:</b> {text.get(context.user_data.get('baby_seat'), context.user_data.get('baby_seat'))}
🗒️ <b>{text['notes']}:</b> {context.user_data.get('notes')}
"""

    keyboard = [
        [InlineKeyboardButton(text["confirm"], callback_data="confirm_booking")],
        [InlineKeyboardButton(text["cancel"], callback_data="cancel_booking")],
        [InlineKeyboardButton("⬅️ " + text["back"], callback_data="back_to_notes")]
    ]
    await update.message.reply_html(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return "WAITING_CONFIRMATION"
