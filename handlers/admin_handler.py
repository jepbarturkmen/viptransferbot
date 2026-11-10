import asyncio
import logging

import psycopg
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from persistence import InvalidStatusTransition

log = logging.getLogger(__name__)
VALID_STATUSES = {"pending", "confirmed", "cancelled"}


async def _authorized(update: Update) -> bool:
    user = update.effective_user
    if user and user.id == ADMIN_USER_ID:
        return True
    await update.effective_message.reply_text("You are not authorized to use this command.")
    log.warning("Rejected admin command from Telegram user %s", user.id if user else "unknown")
    return False


async def _database_error(update: Update) -> None:
    log.exception("Admin command failed due to a PostgreSQL error")
    await update.effective_message.reply_text(
        "The booking database is temporarily unavailable. Please try again."
    )


async def list_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    repository = context.application.bot_data["booking_repository"]
    try:
        bookings = await asyncio.to_thread(repository.list_bookings, 15)
    except psycopg.Error:
        await _database_error(update)
        return

    if not bookings:
        await update.effective_message.reply_text("No bookings have been submitted.")
        return
    lines = ["Recent bookings:"]
    for booking in bookings:
        data = booking["booking_data"]
        lines.append(
            f"{booking['booking_id']} | {booking['status']} | "
            f"{data.get('date', '-')} {data.get('time', '-')} | {data.get('name', '-')}"
        )
    await update.effective_message.reply_text("\n".join(lines))


async def get_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Usage: /booking <booking-id>")
        return

    repository = context.application.bot_data["booking_repository"]
    try:
        booking = await asyncio.to_thread(repository.get_booking, context.args[0])
    except ValueError:
        await update.effective_message.reply_text("That booking ID is not valid.")
        return
    except psycopg.Error:
        await _database_error(update)
        return
    if booking is None:
        await update.effective_message.reply_text("Booking not found.")
        return

    data = booking["booking_data"]
    await update.effective_message.reply_text(
        "\n".join(
            (
                f"Booking ID: {booking['booking_id']}",
                f"Status: {booking['status']}",
                f"Name: {data.get('name', '-')}",
                f"Phone: {data.get('phone', '-')}",
                f"From: {data.get('pickup_location', '-')}",
                f"To: {data.get('dropoff_location', '-')}",
                f"Passengers: {data.get('passengers', '-')}",
                f"Date/time: {data.get('date', '-')} {data.get('time', '-')}",
                f"Flight: {data.get('flight_number') or '-'}",
                f"Meeting time: {data.get('meeting_time') or '-'}",
                f"Telegram user ID: {booking['user_id']}",
            )
        )
    )


async def update_booking_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not await _authorized(update):
        return
    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /booking_status <booking-id> <pending|confirmed|cancelled>"
        )
        return

    booking_id, status = context.args
    status = status.lower()
    if status not in VALID_STATUSES:
        await update.effective_message.reply_text(
            "Status must be pending, confirmed, or cancelled."
        )
        return

    repository = context.application.bot_data["booking_repository"]
    try:
        updated = await asyncio.to_thread(
            repository.update_booking_status, booking_id, status
        )
    except InvalidStatusTransition as error:
        await update.effective_message.reply_text(str(error))
        return
    except ValueError:
        await update.effective_message.reply_text("That booking ID is not valid.")
        return
    except psycopg.Error:
        await _database_error(update)
        return
    if not updated:
        await update.effective_message.reply_text("Booking not found.")
        return

    log.info("Admin updated booking %s status to %s", booking_id, status)
    await update.effective_message.reply_text(
        f"Booking {booking_id} status updated to {status}."
    )
