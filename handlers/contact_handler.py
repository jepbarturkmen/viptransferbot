
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import ADMIN_USER_ID
from languages import load_translations

CONTACT_ASK_MESSAGE = 200

async def ask_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "tr")
    text = load_translations(lang)

    keyboard = [[InlineKeyboardButton(text["back"], callback_data="back_to_menu")]]
    await query.message.reply_text(
        f"{text['contact_dispatcher']}\nLütfen mesajınızı yazın:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONTACT_ASK_MESSAGE

async def receive_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "tr")
    text = load_translations(lang)
    user = update.message.from_user

    user_msg = update.message.text
    message = (
        "📨 Yeni mesaj iletildi:\n\n"
        f"👤 @{user.username or user.first_name}\n"
        f"📝 {user_msg}"
    )
    await context.bot.send_message(chat_id=ADMIN_USER_ID, text=message)
    await update.message.reply_text("✅ Mesajınız yetkiliye iletildi. En kısa sürede dönüş yapılacaktır.")
    return ConversationHandler.END

contact_dispatcher_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_contact_message, pattern="^contact_dispatcher$")],
    states={
        CONTACT_ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_message)],
    },
    fallbacks=[],
    allow_reentry=True
)
