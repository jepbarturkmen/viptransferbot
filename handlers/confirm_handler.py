import asyncio
import logging

import psycopg
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_USER_ID
from handlers.states import SHOW_SUMMARY
from utils.booking import validate_booking
from utils.language_loader import load_translations
from utils.sheet_exporter import retry_pending_sheet_exports
from utils.state import reset_booking

log = logging.getLogger(__name__)


async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = context.user_data
    lang = user_data.get("language", "tr")
    tr = load_translations(lang)

    booking = {
        key: user_data.get(key, "")
        for key in (
            "name",
            "phone",
            "pickup_location",
            "dropoff_location",
            "passengers",
            "baby_seat",
            "notes",
            "date",
            "time",
            "flight_number",
            "meeting_time",
        )
    }
    booking["telegram_user_id"] = user_id

    try:
        validate_booking(booking)
    except ValueError:
        await query.message.reply_text(
            tr.get("booking.invalid", "Some booking details are missing or invalid. Please review them.")
        )
        return SHOW_SUMMARY

    repository = context.application.bot_data["booking_repository"]
    try:
        booking_id = await asyncio.to_thread(repository.create_booking, user_id, booking)
    except psycopg.Error:
        log.exception("Could not save booking for Telegram user %s", user_id)
        await query.message.reply_text(
            tr.get(
                "booking.save_failed",
                "We couldn't save your booking right now. Please try again.",
            )
        )
        return SHOW_SUMMARY

    admin_message = (
        "New VIP transfer booking\n"
        f"Booking ID: {booking_id}\n"
        f"Name: {booking['name']}\n"
        f"Phone: {booking['phone']}\n"
        f"From: {booking['pickup_location']}\n"
        f"To: {booking['dropoff_location']}\n"
        f"Passengers: {booking['passengers']}\n"
        f"Baby seat: {booking['baby_seat'] or '-'}\n"
        f"Extra requests: {booking['notes'] or '-'}\n"
        f"Date/time: {booking['date']} {booking['time']}\n"
        f"Flight: {booking['flight_number'] or '-'}\n"
        f"Meeting time: {booking['meeting_time'] or '-'}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_message)
    except TelegramError:
        log.exception("Booking %s was saved but admin notification failed", booking_id)

    context.job_queue.run_once(
        retry_pending_sheet_exports,
        when=0,
        name=f"sheet-export-{booking_id}",
    )
    reset_booking(user_data)
    await query.message.reply_text(
        tr.get(
            "booking.submitted",
            "Thanks! Your booking request has been received ✅",
        )
    )
    log.info("Booking %s saved for Telegram user %s", booking_id, user_id)
    return ConversationHandler.END


async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    reset_booking(context.user_data)
    tr = load_translations(context.user_data.get("language", "tr"))
    message = query.message if query else update.effective_message
    await message.reply_text(
        tr.get("booking.cancelled", "Your booking was cancelled.")
    )
    return ConversationHandler.END
