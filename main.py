import os
import logging
import asyncio
import logging
logging.getLogger("vipbot").info("ENV token var mı? %s", "yes" if TOKEN else "no")

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
# LOG_LEVEL env ile yönetilebilir; varsayılan WARNING
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
level = getattr(logging, LOG_LEVEL, logging.WARNING)
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
from config import TOKEN
from handlers.start_handler import start, language_selected, show_main_menu
from handlers.booking_handler import booking_conversation_handler
from handlers.upload_pdf import ask_for_pdf, receive_pdf
from handlers.contact_dispatcher import ask_contact, receive_contact_message


# -----------------------------
# BASİT SAĞLIK / TEST KOMUTLARI (opsiyonel)
# -----------------------------
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")


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

def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN (config.TOKEN) eksik!")

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)  # webhook temizliği
        .build()
    )

    # Hata yakalayıcı
    app.add_error_handler(error_handler)

    # /start
    app.add_handler(CommandHandler("start", start))
    # /ping (opsiyonel test komutu)
    app.add_handler(CommandHandler("ping", ping))

    # Dil seçimi
    app.add_handler(CallbackQueryHandler(language_selected, pattern=r"^(tr|en|ru|de|ar)$"))

    # Ana menü (geri)
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$"))

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
        fallbacks=[CallbackQueryHandler(show_main_menu, pattern=r"^back_to_menu$")],
        allow_reentry=True,
    )
    app.add_handler(upload_conv)

    # Dispatcher ile iletişim diyalogu
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


# -----------------------------
# MAIN
# -----------------------------
def main() -> None:
    app = build_app()

    # (Ek güvence) Uygulama başlamadan önce webhook silme – post_init zaten yapacak,
    # ama Railway’de nadiren loop timing sorunları olursa diye ek bir garanti:
    async def _ensure_delete_webhook():
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            log.info("Webhook (pre-run) silindi (ek garanti).")
        except Exception as e:
            log.warning("Webhook pre-run silme denemesi atlandı: %s", e)

    asyncio.get_event_loop().run_until_complete(_ensure_delete_webhook())

    log.info("Polling başlıyor…")
    # allowed_updates=[]: varsayılan tipler; performans için yeterli
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":
    main()
