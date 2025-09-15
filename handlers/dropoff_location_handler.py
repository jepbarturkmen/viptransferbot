from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.state import UserState
from utils.excel_reader import get_airport_list, get_hotel_list
from utils.date_picker import generate_date_keyboard
from utils.time_picker import generate_time_keyboard
from handlers.extra_info_handler import ask_flight_number_if_airport, ask_meeting_time
from handlers.states import WAITING_DROPOFF_CATEGORY, WAITING_DROPOFF_LOCATION, ASK_DATE, WAITING_DATE, ASK_TIME, WAITING_TIME, ASK_PASSENGER_COUNT, WAITING_NAME

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

async def ask_dropoff_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)

    kb = [[InlineKeyboardButton(tr.get("booking.to_airport","To Airport"), callback_data="dropoff_category_airport"),
           InlineKeyboardButton(tr.get("booking.to_hotel","To Hotel"), callback_data="dropoff_category_hotel")],
          [InlineKeyboardButton(tr.get("booking.to_aratransfer","Mid-route (Custom)"), callback_data="dropoff_category_custom")],
          [InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="back_to_menu")]]
    await query.message.edit_text(tr.get("booking.ask_dropoff_type","Where is the drop-off?"), reply_markup=InlineKeyboardMarkup(kb))
    return WAITING_DROPOFF_CATEGORY

async def ask_dropoff_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    data = query.data

    kb = []
    if data == "dropoff_category_airport":
        for name in get_airport_list():
            kb.append([InlineKeyboardButton(name, callback_data=f"dropoff_loc:{name}")])
    elif data == "dropoff_category_hotel":
        for name in get_hotel_list():
            kb.append([InlineKeyboardButton(name, callback_data=f"dropoff_loc:{name}")])
    else:
        # custom address; user should type text, but also provide a hint button
        await query.message.edit_text(tr.get("booking.ask_dropoff_location","Choose or enter the drop-off location:"))
        return WAITING_DROPOFF_LOCATION

    kb.append([InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="back_to_menu")])
    await query.message.edit_text(tr.get("booking.ask_dropoff_location","Choose the drop-off location:"),
                                  reply_markup=InlineKeyboardMarkup(kb))
    return WAITING_DROPOFF_LOCATION

async def receive_dropoff_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        lang = UserState.get(user_id).get("language", "en")
        tr = load_translations(lang)
        data = query.data
        if data.startswith("dropoff_loc:"):
            loc = data.split("dropoff_loc:",1)[1]
        else:
            loc = data
        UserState.set(user_id, "dropoff_location", loc)
        return await ask_date(update, context)
    else:
        # user typed address
        user_id = update.effective_user.id
        lang = UserState.get(user_id).get("language", "en")
        tr = load_translations(lang)
        loc = (update.message.text or "").strip()
        if not loc:
            await update.message.reply_text(tr.get("booking.ask_dropoff_location","Choose or enter the drop-off location:"))
            return WAITING_DROPOFF_LOCATION
        UserState.set(user_id, "dropoff_location", loc)
        return await ask_date(update, context)

async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    kb = generate_date_keyboard(lang_code=lang, days=90)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(tr.get("booking.ask_date","Select date:"), reply_markup=kb)
    else:
        await update.message.reply_text(tr.get("booking.ask_date","Select date:"), reply_markup=kb)
    return WAITING_DATE

async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    data = q.data  # "date_YYYY-MM-DD (...)"
    picked = data.replace("date_","")
    date_only = picked.split(" ")[0]
    UserState.set(user_id, "date", date_only)
    kb = generate_time_keyboard()
    await q.message.edit_text(tr.get("booking.ask_time","Select time:"), reply_markup=kb)
    return WAITING_TIME

async def back_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Go back to date picker from time picker
    if update.callback_query:
        await update.callback_query.answer()
    return await ask_date(update, context)

async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)
    picked = q.data.replace("time_","")
    UserState.set(user_id, "time", picked)
# proceed to flight/meeting steps
state = await ask_flight_number_if_airport(update, context)
if state is None:
    state = await ask_meeting_time(update, context)
return state

async def receive_passenger_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)

    pax = query.data.replace("pax_","")
    UserState.set(user_id, "passengers", pax)

    # After pax, ask for name
    from handlers.passenger_info_handler import ask_name
    return await ask_name(update, context)
