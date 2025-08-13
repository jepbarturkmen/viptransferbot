
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import ADMIN_USER_ID
from languages import load_translations

UPLOAD_WAITING_FILE = 100

async def ask_upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "tr")
    text = load_translations(lang)

    keyboard = [[InlineKeyboardButton(text["back"], callback_data="back_to_menu")]]
    await query.message.reply_text(
        f"{text['upload_pdf']}\n(PDF, JPG veya PNG dosyası yükleyin)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return UPLOAD_WAITING_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "tr")
    text = load_translations(lang)

    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    if not file:
        await update.message.reply_text("Yalnızca PDF veya görsel (JPG/PNG) dosya kabul edilir.")
        return UPLOAD_WAITING_FILE

    telegram_file = await file.get_file()
    await context.bot.send_document(chat_id=ADMIN_USER_ID, document=telegram_file.file_id, caption="Yeni yükleme")
    await update.message.reply_text("✅ Dosyanız başarıyla alındı. Teşekkür ederiz.")
    return ConversationHandler.END

upload_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_upload_file, pattern="^upload_pdf$")],
    states={
        UPLOAD_WAITING_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO, receive_file)],
    },
    fallbacks=[],
    allow_reentry=True
)
