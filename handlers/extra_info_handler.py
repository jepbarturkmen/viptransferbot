
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.state import UserState
from handlers.states import (
    ASK_FLIGHT_NUMBER, WAITING_FLIGHT_NUMBER,
    ASK_MEETING_TIME, WAITING_MEETING_TIME,
    ASK_PASSENGER_COUNT,
)

def _meeting_keyboard():
    times = [f"{h:02d}:{m:02d}" for h in range(0,24) for m in (0,30)]
    keyboard, row = [], []
    for i, t in enumerate(times):
        row.append(InlineKeyboardButton(t, callback_data=f"meet_{t}"))
        if len(row) == 4:
            keyboard.append(row); row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Skip ➡️", callback_data="meet_skip")])
    return InlineKeyboardMarkup(keyboard)

def _pax_keyboard(tr):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1", callback_data="pax_1"),
         InlineKeyboardButton("2", callback_data="pax_2"),
         InlineKeyboardButton("3", callback_data="pax_3"),
         InlineKeyboardButton("4", callback_data="pax_4"),
         InlineKeyboardButton("5", callback_data="pax_5")],
        [InlineKeyboardButton("5–15", callback_data="pax_5-15"),
         InlineKeyboardButton("15+", callback_data="pax_15plus")],
        [InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="back_to_menu")]
    ])

async def ask_flight_number_if_airport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)

    pick = context.user_data.get("pickup_category", "")
    drop = context.user_data.get("dropoff_category", "")
    airport_involved = ("pickup_airport" in (pick or "")) or ("dropoff_category_airport" in (drop or ""))

    msg = update.callback_query.message if update.callback_query else update.effective_message

    if airport_involved:
        await msg.reply_text(tr.get("extra.ask_flight_no", "Please enter flight number (e.g., TK123). You can also Skip."),
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr.get("app.skip","Skip ➡️"), callback_data="flight_skip")]]))
        return WAITING_FLIGHT_NUMBER
    return await ask_meeting_time(update, context)

async def receive_flight_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    if update.callback_query:
        q = update.callback_query
        await q.answer()
        if q.data == "flight_skip":
            UserState.set(user_id, "flight_number", None)
            await q.message.reply_text(tr.get("extra.flight_saved","Saved ✅"))
            return await ask_meeting_time(update, context)
        await q.message.reply_text(tr.get("extra.flight_saved","Saved ✅"))
        return await ask_meeting_time(update, context)
    else:
        msg = update.effective_message
        text = (msg.text or "").strip()
        if text:
            UserState.set(user_id, "flight_number", text)
        await msg.reply_text(tr.get("extra.flight_saved","Saved ✅"))
        return await ask_meeting_time(update, context)

async def ask_meeting_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    msg = update.callback_query.message if update.callback_query else update.effective_message
    await msg.reply_text(tr.get("extra.ask_meeting_time","Please select meeting time"),
                         reply_markup=_meeting_keyboard())
    return WAITING_MEETING_TIME

async def receive_meeting_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    data = q.data
    if data == "meet_skip":
        UserState.set(user_id, "meeting_time", None)
    elif data.startswith("meet_"):
        mt = data.replace("meet_","",1)
        UserState.set(user_id, "meeting_time", mt)
    await q.message.reply_text(tr.get("extra.meeting_saved","Saved ✅"))
    await q.message.edit_text(tr.get("booking.ask_pax","How many passengers?"), reply_markup=_pax_keyboard(tr))
    return ASK_PASSENGER_COUNT
