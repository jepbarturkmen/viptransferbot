from utils.state import UserState

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_USER_ID
from languages import load_translations

ASK_FILE = 1

async def ask_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = UserState.get(update.effective_user.id).get("language", context.user_data.get("lang","tr"))
    tr = load_translations(lang)
    await query.message.reply_text(tr.get("upload_prompt","Lütfen PDF veya görsel yükleyin."),
                                   reply_markup=None)
    return ASK_FILE

async def receive_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = UserState.get(update.effective_user.id).get("language", context.user_data.get("lang","tr"))
    tr = load_translations(lang)

    if update.message.document:
        doc = update.message.document
        await context.bot.send_document(chat_id=ADMIN_USER_ID, document=doc.file_id,
            caption=tr.get("upload_forwarded_caption","Yeni belge yüklendi."))
        await update.message.reply_text(tr.get("upload_received","Belgeniz alındı. Teşekkürler!"))
        return ConversationHandler.END
    elif update.message.photo:
        photo = update.message.photo[-1]
        await context.bot.send_photo(chat_id=ADMIN_USER_ID, photo=photo.file_id,
            caption=tr.get("upload_forwarded_caption","Yeni görsel yüklendi."))
        await update.message.reply_text(tr.get("upload_received","Belgeniz alındı. Teşekkürler!"))
        return ConversationHandler.END
    else:
        await update.message.reply_text(tr.get("upload_only_pdf","Lütfen PDF/JPG/PNG gönderin."))
        return ASK_FILE
