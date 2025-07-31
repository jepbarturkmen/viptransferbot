import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
import telegram.error
import asyncio

# Telegram ayarları
BOT_TOKEN = "7969003527:AAEaOwFnoC7O4dxoRCooA8Lvz94HWntPIc4"
DISPATCHER_ID = 8067876866

# Excel dosyalarından verileri oku
hotels_df = pd.read_excel("hotels.xlsx")
airports_df = pd.read_excel("airports.xlsx")

# Geri butonu
def back_button(data):
    return [InlineKeyboardButton("⬅️ Geri", callback_data=f"back_{data}")]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🇹🇷 Türkçe", callback_data='lang_tr'),
        InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
        InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')
    ]]
    await update.message.reply_text("🌍 Please choose your language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    context.user_data['lang'] = query.data[-2:]
    context.user_data['step'] = 'awaiting_name'
    await query.edit_message_text("👤 Lütfen adınızı ve soyadınızı yazınız:")

async def handle_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('step') == 'awaiting_name':
        context.user_data['fullname'] = update.message.text
        context.user_data['step'] = None
        keyboard = [
            [InlineKeyboardButton("📝 Yeni Rezervasyon", callback_data='new_booking')],
            [InlineKeyboardButton("📎 PDF Yükle", callback_data='upload_pdf')],
            [InlineKeyboardButton("📞 İletişime Geç", callback_data='contact_dispatch')]
        ]
        await update.message.reply_text("📋 Ana Menü:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    if query.data == "new_booking":
        context.user_data['step'] = 'select_city'
        cities = sorted(hotels_df["City"].unique())
        keyboard = [[InlineKeyboardButton(city, callback_data=f"city_{city}")] for city in cities]
        await query.edit_message_text("🏙️ Lütfen şehir seçiniz:", reply_markup=InlineKeyboardMarkup(keyboard + [back_button("menu")]))
    elif query.data == "upload_pdf":
        context.user_data['awaiting_pdf'] = True
        await query.edit_message_text("📎 Lütfen PDF dosyanızı gönderin.")
    elif query.data == "contact_dispatch":
        await query.edit_message_text("☎️ Yetkiliye bağlanılıyor...")
        user = query.from_user
        await context.bot.send_message(chat_id=DISPATCHER_ID, text=f"🚨 Kullanıcı iletişim talep etti: @{user.username} ({user.id})")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_pdf'):
        file = update.message.document
        if file.mime_type == 'application/pdf':
            await context.bot.send_document(chat_id=DISPATCHER_ID, document=file.file_id, caption=f"📄 PDF: @{update.effective_user.username}")
            await update.message.reply_text("✅ PDF başarıyla iletildi.")
        else:
            await update.message.reply_text("⚠️ Lütfen sadece PDF dosyası gönderin.")
        context.user_data['awaiting_pdf'] = False

async def city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    city = query.data.split("_", 1)[1]
    context.user_data['city'] = city
    context.user_data['step'] = 'select_airport'
    airports = airports_df[airports_df['City'] == city]['Airport Name'].tolist()
    keyboard = [[InlineKeyboardButton(a, callback_data=f"airport_{a}")] for a in airports]
    await query.edit_message_text(f"✈️ {city} için havalimanı seçin:", reply_markup=InlineKeyboardMarkup(keyboard + [back_button("city")]))

async def airport_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    airport = query.data.split("_", 1)[1]
    context.user_data['airport'] = airport
    context.user_data['step'] = 'select_hotel'
    hotels = hotels_df[hotels_df['City'] == context.user_data['city']]['Hotel Name'].tolist()
    keyboard = [[InlineKeyboardButton(h, callback_data=f"hotel_{h}")] for h in hotels]
    await query.edit_message_text("🏨 Otel seçin:", reply_markup=InlineKeyboardMarkup(keyboard + [back_button("airport")]))

async def hotel_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    hotel = query.data.split("_", 1)[1]
    context.user_data['hotel'] = hotel
    keyboard = [
        [InlineKeyboardButton("1 kişi", callback_data="pax_1")],
        [InlineKeyboardButton("2-4 kişi", callback_data="pax_2_4")],
        [InlineKeyboardButton("5+ kişi", callback_data="pax_5")]
    ]
    await query.edit_message_text("👥 Yolcu sayısını seçin:", reply_markup=InlineKeyboardMarkup(keyboard + [back_button("hotel")]))

async def pax_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    pax = query.data.split("_", 1)[1].replace("_", "-")
    context.user_data['pax'] = pax
    keyboard = [
        [InlineKeyboardButton("Sedan", callback_data="car_sedan")],
        [InlineKeyboardButton("VIP Van", callback_data="car_vipvan")],
        [InlineKeyboardButton("SUV", callback_data="car_suv")]
    ]
    await query.edit_message_text("🚘 Araç tipi seçin:", reply_markup=InlineKeyboardMarkup(keyboard + [back_button("pax")]))

async def car_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    car = query.data.split("_", 1)[1]
    context.user_data['car'] = car
    date = datetime.now().strftime("%Y-%m-%d")
    context.user_data['date'] = date
    summary = (
        f"✅ Rezervasyon Özeti:\n"
        f"👤 Ad Soyad: {context.user_data['fullname']}\n"
        f"🏙️ Şehir: {context.user_data['city']}\n"
        f"✈️ Havalimanı: {context.user_data['airport']}\n"
        f"🏨 Otel: {context.user_data['hotel']}\n"
        f"👥 Yolcu: {context.user_data['pax']}\n"
        f"🚘 Araç: {context.user_data['car']}\n"
        f"📅 Tarih: {context.user_data['date']}"
    )
    keyboard = [[InlineKeyboardButton("✅ Onayla ve Gönder", callback_data="confirm")]]
    await query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard + [back_button("car")]))

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    summary = (
        f"📦 Yeni VIP Transfer Talebi:\n"
        f"👤 {context.user_data['fullname']}\n"
        f"🏙️ {context.user_data['city']}\n"
        f"✈️ {context.user_data['airport']}\n"
        f"🏨 {context.user_data['hotel']}\n"
        f"👥 {context.user_data['pax']}\n"
        f"🚘 {context.user_data['car']}\n"
        f"📅 {context.user_data['date']}"
    )
    await context.bot.send_message(chat_id=DISPATCHER_ID, text=summary)
    await query.edit_message_text("✅ Talebiniz başarıyla iletildi!")
    keyboard = [
        [InlineKeyboardButton("📝 Yeni Rezervasyon", callback_data='new_booking')],
        [InlineKeyboardButton("📎 PDF Yükle", callback_data='upload_pdf')],
        [InlineKeyboardButton("📞 İletişime Geç", callback_data='contact_dispatch')]
    ]
    await context.bot.send_message(chat_id=query.from_user.id, text="🔁 Yeni işlem yapmak ister misiniz?", reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data.clear()

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        pass
    dest = query.data.split("_", 1)[1]
    if dest == "menu":
        await language_selected(update, context)
    elif dest == "city":
        await menu_selected(update, context)
    elif dest == "airport":
        await city_selected(update, context)
    elif dest == "hotel":
        await airport_selected(update, context)
    elif dest == "pax":
        await hotel_selected(update, context)
    elif dest == "car":
        await pax_selected(update, context)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(menu_selected, pattern="^(new_booking|upload_pdf|contact_dispatch)$"))
    app.add_handler(CallbackQueryHandler(city_selected, pattern="^city_"))
    app.add_handler(CallbackQueryHandler(airport_selected, pattern="^airport_"))
    app.add_handler(CallbackQueryHandler(hotel_selected, pattern="^hotel_"))
    app.add_handler(CallbackQueryHandler(pax_selected, pattern="^pax_"))
    app.add_handler(CallbackQueryHandler(car_selected, pattern="^car_"))
    app.add_handler(CallbackQueryHandler(confirm, pattern="^confirm$"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_"))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fullname))

    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
