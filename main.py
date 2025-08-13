from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import os
import logging

# LOG_LEVEL env ile yönetilebilir; varsayılan WARNING
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
level = getattr(logging, LOG_LEVEL, logging.WARNING)

logging.basicConfig(
    level=level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Gürültülü logger'ları kıstık (HTTP istekleri, scheduler vs.)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

from config import TOKEN
from handlers.start_handler import start, language_selected, show_main_menu
from handlers.booking_handler import booking_conversation_handler
from handlers.upload_pdf import ask_for_pdf, receive_pdf
from handlers.contact_dispatcher import ask_contact, receive_contact_message

def build_app() -> Application:
    app = Application.builder().token(TOKEN).build()

    # Logging
    logging.basicConfig(level=logging.INFO)

    async def error_handler(update, context):
        logging.exception("Unhandled error: %s", context.error)

    app.add_error_handler(error_handler)

    # /start
    app.add_handler(CommandHandler("start", start))

    # Language selection
    app.add_handler(CallbackQueryHandler(language_selected, pattern=r"^(tr|en|ru|de|ar)$"))

    # Main menu (back)
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$"))

    # Booking conversation
    app.add_handler(booking_conversation_handler)

    # Upload conversation
    upload_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_pdf, pattern=r"^upload_pdf$")],
        states={
            1: [
                MessageHandler((filters.Document.ALL | filters.PHOTO), receive_pdf),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pdf)
            ]
        },
        fallbacks=[CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$")],
        allow_reentry=True,
    )
    app.add_handler(upload_conv)

    # Contact conversation
    contact_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_contact, pattern=r"^contact_dispatcher$")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_message)]
        },
        fallbacks=[CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$")],
        allow_reentry=True,
    )
    app.add_handler(contact_conv)

    return app

def main() -> None:
    app = build_app()
    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
