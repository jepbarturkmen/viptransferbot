import asyncio
import logging

import psycopg

from sheet_service import SheetExportError, append_booking_to_sheet

log = logging.getLogger(__name__)
_export_lock = asyncio.Lock()


async def retry_pending_sheet_exports(context) -> None:
    async with _export_lock:
        await _retry_pending_sheet_exports(context)


async def _retry_pending_sheet_exports(context) -> None:
    repository = context.application.bot_data["booking_repository"]
    try:
        bookings = await asyncio.to_thread(repository.pending_sheet_exports)
    except psycopg.Error:
        log.exception("Could not load pending Google Sheets exports")
        return

    for booking in bookings:
        booking_id = booking["booking_id"]
        try:
            await asyncio.to_thread(
                append_booking_to_sheet, booking["booking_data"], booking_id
            )
        except SheetExportError as error:
            await asyncio.to_thread(
                repository.mark_sheet_export_failed, booking_id, str(error)
            )
            log.exception("Google Sheets export failed for booking %s", booking_id)
        else:
            await asyncio.to_thread(repository.mark_sheet_exported, booking_id)
            log.info("Google Sheets export completed for booking %s", booking_id)
