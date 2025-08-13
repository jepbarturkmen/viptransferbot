
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.language_loader import load_translations
from utils.state import UserState, reset_booking
from utils.excel_reader import get_airport_list, get_hotel_list
from handlers.dropoff_location_handler import ask_dropoff_type
from handlers.states import WAITING_PICKUP_CATEGORY, WAITING_PICKUP_LOCATION, WAITING_DROPOFF_CATEGORY

# States expected by booking_conversation_handler
STATE_WAITING_PICKUP_CATEGORY = "WAITING_PICKUP_CATEGORY"
STATE_WAITING_PICKUP_LOCATION = "WAITING_PICKUP_LOCATION"
STATE_WAITING_DROPOFF_CATEGORY = "WAITING_DROPOFF_CATEGORY"

async def ask_pickup_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    reset_booking(user_id)
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)

    keyboard = [
        [InlineKeyboardButton(tr.get("from_airport","From Airport"), callback_data="pickup_airport")],
        [InlineKeyboardButton(tr.get("from_hotel","From Hotel"), callback_data="pickup_hotel")],
        [InlineKeyboardButton(tr.get("from_aratransfer","From Mid-Transfer"), callback_data="pickup_aratransfer")],
        [InlineKeyboardButton("⬅️ " + tr.get("back","Back"), callback_data="back_to_menu")]
    ]
    await query.message.edit_text(tr.get("select_pickup_type","Select pickup type"), reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_PICKUP_CATEGORY

async def ask_pickup_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang = UserState.get(user_id).get("language", "en")
    tr = load_translations(lang)

    choice = query.data
    context.user_data["pickup_category"] = choice

    if choice == "pickup_airport":
        items = get_airport_list()
        buttons = [[InlineKeyboardButton(name, callback_data=f"pickup_loc_{name}")] for name in items]
        buttons.append([InlineKeyboardButton("⬅️ " + tr.get("back","Back"), callback_data="pickup_type_back")])
        await query.message.edit_text(tr.get("select_pickup_location","Choose pickup location"), reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PICKUP_LOCATION

    if choice == "pickup_hotel":
        items = get_hotel_list()
        buttons = [[InlineKeyboardButton(name, callback_data=f"pickup_loc_{name}")] for name in items]
        buttons.append([InlineKeyboardButton("⬅️ " + tr.get("back","Back"), callback_data="pickup_type_back")])
        await query.message.edit_text(tr.get("select_pickup_location","Choose pickup location"), reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PICKUP_LOCATION

    if choice == "pickup_aratransfer":
        # Ask user to type address as free text
        await query.message.edit_text(tr.get("enter_pickup_address","Please enter the pickup address"))
        return WAITING_PICKUP_LOCATION

    if choice == "pickup_type_back":
        return await ask_pickup_type(update, context)

    # Fallback
    await query.message.edit_text("Invalid selection")
    return WAITING_PICKUP_CATEGORY

async def receive_pickup_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This handler handles both callback (user picked from list) and text (user typed address)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        lang = UserState.get(user_id).get("language", "en")
        tr = load_translations(lang)

        data = query.data
        if data == "pickup_type_back":
            return await ask_pickup_type(update, context)

        if data.startswith("pickup_loc_"):
            loc = data.replace("pickup_loc_", "")
            UserState.set(user_id, "pickup_location", loc)
            await query.message.edit_text(f"{tr.get('pickup_confirmed','Pickup location saved')} ✅\n{loc}")
            # Move to dropoff type immediately
            await ask_dropoff_type(update, context)
            return WAITING_DROPOFF_CATEGORY

        # Unexpected callback here
        await query.message.edit_text("Invalid pickup location selection")
        return WAITING_PICKUP_LOCATION

    else:
        # Text message (address typed)
        user_id = update.effective_user.id
        lang = UserState.get(user_id).get("language", "en")
        tr = load_translations(lang)
        loc = (update.message.text or "").strip()
        if not loc:
            await update.message.reply_text(tr.get("enter_pickup_address","Please enter the pickup address"))
            return WAITING_PICKUP_LOCATION
        UserState.set(user_id, "pickup_location", loc)
        await update.message.reply_text(f"{tr.get('pickup_confirmed','Pickup location saved')} ✅\n{loc}")
        # Proceed to dropoff
        await ask_dropoff_type(update, context)
        return WAITING_DROPOFF_CATEGORY
