import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler
from utils.language_loader import load_translations
from config import ADMIN_USER_ID

log = logging.getLogger(__name__)


async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inform user and notify admin when 'Contact Dispatcher' is pressed."""
    # It is triggered via callback button
    query = update.callback_query
    if query:
        await query.answer()

    uid = update.effective_user.id
    user = update.effective_user

    # Language
    lang = context.user_data.get("language", "tr")
    tr = load_translations(lang)

    # 1) Inform the user in their language
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=tr.get("contact.message_to_dispatcher", "The operator will contact you as soon as possible.")
    )

    # 2) Notify admin (non-fatal if it fails)
    full_name = f"{(user.first_name or '')} {(user.last_name or '')}".strip()
    username = f"@{user.username}" if user.username else "—"

    admin_text = f"""📥 <b>Yeni İletişim Talebi</b>

👤 <b>Kullanıcı:</b> {full_name} {username}
🆔 <b>User ID:</b> {uid}
🌐 <b>Dil:</b> {lang}
⏳ Kullanıcı operatörün iletişime geçmesini bekliyor."""

    try:
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_text)
    except TelegramError:
        log.exception("Admin notification failed for contact request from user %s", uid)

    return ConversationHandler.END

# Backward-compat stub: if conversation expects a follow-up message handler, end gracefully.
async def receive_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = context.user_data.get("language", "tr")
    tr = load_translations(lang)
    await update.message.reply_text(tr.get("contact.message_to_dispatcher", "The operator will contact you as soon as possible."))
    return ConversationHandler.END
