import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.language_loader import load_translations
from utils.state import UserState
from config import ADMIN_USER_ID

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    # language
    lang = UserState.get(uid).get("language", context.user_data.get("lang", "tr"))
    tr = load_translations(lang)

    # gather booking data
    st = UserState.get(uid)
    name = context.user_data.get("name", "")
    phone = context.user_data.get("phone", "")
    from_loc = st.get("pickup_location", "")
    to_loc = st.get("dropoff_location", "")
    pax = st.get("passengers", "")
    baby = context.user_data.get("baby_seat", "")
    extras = context.user_data.get("notes", "")
    date = st.get("date", "")
    time = st.get("time", "")
    flight = st.get("flight", "")

    # build row for Sheets
    row = [name, phone, from_loc, to_loc, pax, baby, extras, date, time, flight, str(uid)]
# Admin message
    admin_message = f"""
📢 <b>Yeni VIP Rezervasyon</b>

👤 <b>Ad Soyad:</b> {name}
📞 <b>Telefon:</b> {phone}
🚖 <b>Nereden:</b> {from_loc}
📍 <b>Nereye:</b> {to_loc}
👥 <b>Kişi Sayısı:</b> {pax}
👶 <b>Bebek Koltuğu:</b> {baby}
🗒️ <b>Ekstra:</b> {extras}
📅 <b>Tarih:</b> {date} {time}
✈️ <b>Uçuş:</b> {flight}
"""
    await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_message, parse_mode="HTML")

    await query.message.reply_text(tr.get("booking_success", tr.get("booking.submitted", "Thanks! Your booking request has been received ✅")))
    return ConversationHandler.END

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Rezervasyon iptal edildi.")
    return ConversationHandler.END
