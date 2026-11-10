
import re
from datetime import date, datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.excel_reader import get_airport_list, get_hotel_list
from handlers.extra_info_handler import ask_flight_number_if_airport, ask_meeting_time
from handlers.passenger_info_handler import ask_name
from handlers.states import (
    WAITING_DROPOFF_CATEGORY,
    WAITING_DROPOFF_LOCATION,
    ASK_DATE, WAITING_DATE,
    ASK_TIME, WAITING_TIME,
    ASK_PASSENGER_COUNT, WAITING_NAME
)

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

def _date_keyboard():
    from utils.date_picker import generate_date_keyboard
    return generate_date_keyboard()

def _time_keyboard_with_back(tr):
    from utils.time_picker import generate_time_keyboard
    base = generate_time_keyboard()
    kb = [list(row) for row in base.inline_keyboard]
    kb = [
        [button for button in row if button.callback_data != "back_to_date"]
        for row in kb
    ]
    kb = [row for row in kb if row]
    kb.append([InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="back_to_date")])
    return InlineKeyboardMarkup(kb)

async def ask_dropoff_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)

    keyboard = [
        [InlineKeyboardButton(tr.get("booking.to_airport","To Airport"), callback_data="dropoff_category_airport"),
         InlineKeyboardButton(tr.get("booking.to_hotel","To Hotel"), callback_data="dropoff_category_hotel")],
        [InlineKeyboardButton(tr.get("booking.to_custom","Other address"), callback_data="dropoff_category_custom")],
        [InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="back_to_menu")]
    ]
    await query.message.edit_text(tr.get("booking.select_dropoff_type","Please select dropoff type"),
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_DROPOFF_CATEGORY

async def ask_dropoff_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)

    choice = query.data
    context.user_data["dropoff_category"] = choice

    if choice == "dropoff_category_airport":
        items = get_airport_list()
        buttons = [[InlineKeyboardButton(name, callback_data=f"dropoff_loc:{name}")] for name in items]
        buttons.append([InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="dropoff_type_back")])
        await query.message.edit_text(tr.get("booking.select_dropoff_airport","Select dropoff airport"),
                                      reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_DROPOFF_LOCATION

    if choice == "dropoff_category_hotel":
        items = get_hotel_list()
        buttons = [[InlineKeyboardButton(name, callback_data=f"dropoff_loc:{name}")] for name in items]
        buttons.append([InlineKeyboardButton(tr.get("app.back","⬅️ Back"), callback_data="dropoff_type_back")])
        await query.message.edit_text(tr.get("booking.select_dropoff_hotel","Select dropoff hotel"),
                                      reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_DROPOFF_LOCATION

    if choice == "dropoff_type_back":
        return await ask_dropoff_type(update, context)
    if choice == "dropoff_category_custom":
        await query.message.edit_text(
            tr.get("booking.ask_custom_address", "Please enter the dropoff address")
        )
        return WAITING_DROPOFF_LOCATION

    await query.message.reply_text(tr.get("app.invalid_option","Invalid option. Please choose again."))
    return WAITING_DROPOFF_CATEGORY

async def receive_dropoff_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "dropoff_type_back":
            return await ask_dropoff_type(update, context)
        if data.startswith("dropoff_loc:"):
            loc = data.split("dropoff_loc:",1)[1]
        else:
            loc = data
        context.user_data["dropoff_location"] = loc
        return await ask_date(update, context)
    else:
        lang = context.user_data.get("language", "en")
        tr = load_translations(lang)
        loc = (update.message.text or "").strip()
        if not loc or len(loc) > 300:
            await update.message.reply_text(tr.get("booking.enter_dropoff_address","Please enter the dropoff address"))
            return WAITING_DROPOFF_LOCATION
        context.user_data["dropoff_location"] = loc
        return await ask_date(update, context)

async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    msg = update.callback_query.message if update.callback_query else update.effective_message
    await msg.reply_text(tr.get("booking.select_date","Please select date"),
                         reply_markup=_date_keyboard())
    return WAITING_DATE

async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    data = q.data
    if data.startswith("date_"):
        picked = data.replace("date_","",1)
        try:
            selected_date = datetime.strptime(picked, "%Y-%m-%d (%a)").date()
        except ValueError:
            selected_date = None
        today = date.today()
        if selected_date is None or not today <= selected_date <= today + timedelta(days=89):
            await q.message.reply_text(
                tr.get("app.invalid_option","Invalid option. Please choose again.")
            )
            return WAITING_DATE
        context.user_data["date"] = picked
        return await ask_time(update, context)
    await q.message.reply_text(tr.get("app.invalid_option","Invalid option. Please choose again."))
    return WAITING_DATE

async def back_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
    return await ask_date(update, context)

async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    msg = update.callback_query.message if update.callback_query else update.effective_message
    await msg.reply_text(tr.get("booking.select_time","Please select time"),
                         reply_markup=_time_keyboard_with_back(tr))
    return WAITING_TIME

async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    data = q.data
    if data == "back_to_date":
        return await ask_date(update, context)
    if data.startswith("time_"):
        picked = data.replace("time_","",1)
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", picked):
            await q.message.reply_text(
                tr.get("app.invalid_option","Invalid option. Please choose again.")
            )
            return WAITING_TIME
        context.user_data["time"] = picked
        next_state = await ask_flight_number_if_airport(update, context)
        if next_state is None:
            next_state = await ask_meeting_time(update, context)
        return next_state
    await q.message.reply_text(tr.get("app.invalid_option","Invalid option. Please choose again."))
    return WAITING_TIME

async def receive_passenger_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    tr = load_translations(lang)
    data = query.data
    val = None
    if data == "pax_15plus":
        val = "15+"
    elif data == "pax_5-15":
        val = "5-15"
    elif data.startswith("pax_"):
        try:
            val = int(data.split("_",1)[1])
        except ValueError:
            val = None
    if val not in (1, 2, 3, 4, 5, "5-15", "15+"):
        await query.message.reply_text(
            tr.get("app.invalid_option","Invalid option. Please choose again.")
        )
        return ASK_PASSENGER_COUNT
    context.user_data["passengers"] = val
    await query.message.reply_text(tr.get("booking.ask_name","Please enter passenger full name"))
    return WAITING_NAME
