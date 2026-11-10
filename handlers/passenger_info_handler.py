from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from handlers.states import WAITING_NAME, WAITING_PHONE, ASK_BABY_SEAT, WAITING_BABY_SEAT, WAITING_NOTES, SHOW_SUMMARY

def _send_summary(update, context, tr):
    user_data = context.user_data
    name = user_data.get('name') or ''
    phone = user_data.get('phone') or ''
    date = user_data.get('date') or ''
    time = user_data.get('time') or ''
    _from = user_data.get('pickup_location') or ''
    _to = user_data.get('dropoff_location') or ''
    pax = user_data.get('passengers') or ''
    baby = context.user_data.get('baby_seat') or ''
    extras = context.user_data.get('notes') or ''
    flight = user_data.get('flight_number') or ''
    meeting_time = user_data.get('meeting_time') or ''
    template = tr.get('booking.summary_text') or 'Name: {name}\nPhone: {phone}\nDate: {date} {time}\nFrom: {from}\nTo: {to}\nPAX: {pax}\nBaby seat: {baby_seat}\nExtras: {extras}\nFlight: {flight}'
    summary = template.format(**{'name': name, 'phone': phone, 'date': date, 'time': time, 'from': _from, 'to': _to, 'pax': pax, 'baby_seat': baby, 'extras': extras, 'flight': flight})
    summary += "\n" + tr.get(
        "booking.summary_meeting_time", "Meeting time: {meeting_time}"
    ).format(meeting_time=meeting_time or "-")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(tr.get('confirm_yes','Confirm'), callback_data='confirm_booking'), InlineKeyboardButton(tr.get('cancel','Cancel'), callback_data='cancel_booking')]])
    return summary, kb


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(tr.get("booking.ask_name","Full name:"))
    else:
        await update.message.reply_text(tr.get("booking.ask_name","Full name:"))
    return WAITING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    if len(name) < 2 or len(name) > 100:
        await update.message.reply_text(
            tr.get("booking.invalid_name", "Please enter a name between 2 and 100 characters.")
        )
        return WAITING_NAME
    context.user_data["name"] = name
    await update.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    return WAITING_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    else:
        await update.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    return WAITING_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = (update.message.text or "").strip()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    digits = "".join(character for character in phone if character.isdigit())
    if not phone or len(phone) > 24 or not 7 <= len(digits) <= 15 or any(
        character not in "+0123456789 ().-" for character in phone
    ):
        await update.message.reply_text(
            tr.get("booking.invalid_phone", "Please enter a valid phone number with country code.")
        )
        return WAITING_PHONE
    context.user_data["phone"] = phone
    # ask baby seat
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(tr.get("yes","Yes"), callback_data="baby_yes"),
         InlineKeyboardButton(tr.get("no","No"), callback_data="baby_no")]
    ])
    await update.message.reply_text(tr.get("booking.ask_baby_seat","Need a baby seat?"), reply_markup=kb)
    return WAITING_BABY_SEAT

async def ask_baby_seat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    if update.callback_query:
        await update.callback_query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(tr.get("yes","Yes"), callback_data="baby_yes"),
             InlineKeyboardButton(tr.get("no","No"), callback_data="baby_no")]
        ])
        await update.callback_query.message.reply_text(tr.get("booking.ask_baby_seat","Need a baby seat?"), reply_markup=kb)
    return WAITING_BABY_SEAT

async def receive_baby_seat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["baby_seat"] = "yes" if query.data == "baby_yes" else "no"
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    kb2 = InlineKeyboardMarkup([[InlineKeyboardButton(tr.get('booking.extras_skip','Skip'), callback_data='notes_skip')]])
    await query.message.reply_text(tr.get('booking.ask_extras','Any extra requests?'), reply_markup=kb2)
    return WAITING_NOTES

async def receive_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = (update.message.text or "").strip()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    if len(notes) > 1000:
        await update.message.reply_text(
            tr.get("booking.invalid", "Please keep extra requests under 1000 characters.")
        )
        return WAITING_NOTES
    context.user_data["notes"] = notes
    summary, kb = _send_summary(update, context, tr)
    await update.message.reply_text(tr.get("booking.summary_title","Booking Summary"))
    await update.message.reply_text(summary, reply_markup=kb)
    return SHOW_SUMMARY


async def receive_notes_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # user pressed Skip button for extras
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data["notes"] = ""
    lang = context.user_data.get("language", _get_lang(update))
    tr = load_translations(lang)
    summary, kb = _send_summary(update, context, tr)
    # edit or send summary
    if update.callback_query:
        await update.callback_query.message.reply_text(tr.get("booking.summary_title","Booking Summary"))
        await update.callback_query.message.reply_text(summary, reply_markup=kb)
    else:
        await update.message.reply_text(tr.get("booking.summary_title","Booking Summary"))
        await update.message.reply_text(summary, reply_markup=kb)
    return SHOW_SUMMARY
