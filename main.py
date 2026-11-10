import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -----------------------------
# LOGGING
# -----------------------------
# LOG_LEVEL env ile yönetilebilir; varsayılan INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
level = getattr(logging, LOG_LEVEL, logging.INFO)
if not isinstance(level, int):
    level = logging.INFO
logging.basicConfig(
    level=level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("vip-bot")

# Gürültülü logger'ları kıs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# -----------------------------
# PROJE İÇİ İTHALLER (AYNEN KALDI)
# -----------------------------
from config import DATABASE_URL, TOKEN
from handlers.admin_handler import get_booking, list_bookings, update_booking_status
from handlers.start_handler import start, language_selected, show_main_menu
from handlers.booking_handler import booking_conversation_handler
from handlers.upload_pdf import ask_for_pdf, receive_pdf
from handlers.contact_dispatcher import ask_contact, receive_contact_message
from persistence import BookingRepository, PostgresPersistence
from utils.sheet_exporter import retry_pending_sheet_exports
from utils.language_loader import load_translations
from utils.state import reset_booking

# -----------------------------
# BASİT SAĞLIK / TEST KOMUTLARI (opsiyonel)
# -----------------------------
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")


async def cancel_other_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_booking(context.user_data)
    tr = load_translations(context.user_data.get("language", "tr"))
    await update.effective_message.reply_text(
        tr.get("booking.cancelled", "Your request was cancelled.")
    )
    return ConversationHandler.END


async def restart_other_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_booking(context.user_data)
    await start(update, context)
    return ConversationHandler.END


async def end_other_flow_at_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)
    return ConversationHandler.END


# -----------------------------
# HATA YAKALAYICI
# -----------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Unhandled error: %s", context.error)


# -----------------------------
# APP KURULUMU
# -----------------------------
async def post_init(app: Application):
    """Polling'den önce Telegram tarafındaki webhook'u kesin sil."""
    me = await app.bot.get_me()
    log.info("Giriş yapıldı: @%s (%s)", me.username, me.id)
    await app.bot.delete_webhook(drop_pending_updates=True)
    log.info("Eski webhook temizlendi, polling'e geçiliyor...")
    if app.job_queue is None:
        raise RuntimeError("The Telegram JobQueue extra is required for Sheet retries.")
    app.job_queue.run_repeating(
        retry_pending_sheet_exports,
        interval=60,
        first=5,
        name="google-sheets-export-retry",
    )

def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN (config.TOKEN) eksik!")
    repository = BookingRepository(DATABASE_URL)
    repository.initialize()
    persistence = PostgresPersistence(repository)

    app = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .post_init(post_init)  # webhook temizliği
        .build()
    )
    app.bot_data["booking_repository"] = repository

    # Hata yakalayıcı
    app.add_error_handler(error_handler)

    # /ping (opsiyonel test komutu)
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("bookings", list_bookings))
    app.add_handler(CommandHandler("booking", get_booking))
    app.add_handler(CommandHandler("booking_status", update_booking_status))

    # Dil seçimi
    app.add_handler(CallbackQueryHandler(language_selected, pattern=r"^(tr|en|ru|de|ar)$"))

    # Rezervasyon diyalogu
    app.add_handler(booking_conversation_handler)

    # PDF/Yükleme diyalogu
    upload_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_pdf, pattern=r"^upload_pdf$")],
        states={
            1: [
                MessageHandler((filters.Document.ALL | filters.PHOTO), receive_pdf),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pdf),
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_other_flow),
            CommandHandler("start", restart_other_flow),
            CallbackQueryHandler(end_other_flow_at_menu, pattern=r"^back_to_menu$"),
        ],
        allow_reentry=True,
        name="upload",
        persistent=True,
    )
    app.add_handler(upload_conv)

    # Dispatcher ile iletişim diyalogu
    contact_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_contact, pattern=r"^contact_dispatcher$")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_message)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_other_flow),
            CommandHandler("start", restart_other_flow),
            CallbackQueryHandler(end_other_flow_at_menu, pattern=r"^back_to_menu$"),
        ],
        allow_reentry=True,
        name="contact",
        persistent=True,
    )
    app.add_handler(contact_conv)

    # Commands/buttons outside a conversation.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$"))

    return app


# -----------------------------
# MAIN
# -----------------------------
def main() -> None:
    app = build_app()
    log.info("Polling başlıyor…")
    # allowed_updates=[]: varsayılan tipler; performans için yeterli
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":
    main()
