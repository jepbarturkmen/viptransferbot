from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.state import UserState
from handlers.states import WAITING_NAME, WAITING_PHONE, ASK_BABY_SEAT, WAITING_BABY_SEAT, WAITING_NOTES, SHOW_SUMMARY

def _send_summary(update, context, tr):
    uid = update.effective_user.id
    st = UserState.get(uid)
    name = context.user_data.get('name') or ''
    phone = context.user_data.get('phone') or ''
    date = st.get('date') or ''
    time = st.get('time') or ''
    _from = st.get('pickup_location') or ''
    _to = st.get('dropoff_location') or ''
    pax = st.get('passengers') or ''
    baby = context.user_data.get('baby_seat') or ''
    extras = context.user_data.get('notes') or ''
    flight = st.get('flight') or ''
    template = tr.get('booking.summary_text') or 'Name: {name}\nPhone: {phone}\nDate: {date} {time}\nFrom: {from}\nTo: {to}\nPAX: {pax}\nBaby seat: {baby_seat}\nExtras: {extras}\nFlight: {flight}'
    summary = template.format(**{'name': name, 'phone': phone, 'date': date, 'time': time, 'from': _from, 'to': _to, 'pax': pax, 'baby_seat': baby, 'extras': extras, 'flight': flight})
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(tr.get('confirm_yes','Confirm'), callback_data='confirm_booking'), InlineKeyboardButton(tr.get('cancel','Cancel'), callback_data='cancel_booking')]])
    return summary, kb


def _get_lang(update):
    uid = (update.effective_user and update.effective_user.id) or None
    if uid is not None:
        return UserState.get(uid).get("language", "en")
    return "en"

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(tr.get("booking.ask_name","Full name:"))
    else:
        await update.message.reply_text(tr.get("booking.ask_name","Full name:"))
    return WAITING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = (update.message.text or "").strip()
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    await update.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    return WAITING_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    else:
        await update.message.reply_text(tr.get("booking.ask_phone","Phone with country code:"))
    return WAITING_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = (update.message.text or "").strip()
    context.user_data["phone"] = phone
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    # ask baby seat
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(tr.get("yes","Yes"), callback_data="baby_yes"),
         InlineKeyboardButton(tr.get("no","No"), callback_data="baby_no")]
    ])
    await update.message.reply_text(tr.get("booking.ask_baby_seat","Need a baby seat?"), reply_markup=kb)
    return WAITING_BABY_SEAT

async def ask_baby_seat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang") or _get_lang(update)
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
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    kb2 = InlineKeyboardMarkup([[InlineKeyboardButton(tr.get('booking.extras_skip','Skip'), callback_data='notes_skip')]])
    await query.message.reply_text(tr.get('booking.ask_extras','Any extra requests?'), reply_markup=kb2)
    return WAITING_NOTES

async def receive_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["notes"] = (update.message.text or "").strip()
    lang = context.user_data.get("lang") or _get_lang(update)
    tr = load_translations(lang)
    summary, kb = _send_summary(update, context, tr)
    await update.message.reply_text(tr.get("booking.summary_title","Booking Summary"))
    await update.message.reply_text(summary, reply_markup=kb)
    return SHOW_SUMMARY


async def receive_notes_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # user pressed Skip button for extras
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data["notes"] = ""
    lang = context.user_data.get("lang") or _get_lang(update)
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
