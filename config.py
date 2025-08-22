# config.py
import os
from dotenv import load_dotenv

# Lokal geliştirme için .env desteği (Railway'de etkisi olmaz ama lokal güzel olur)
load_dotenv()

# Birden fazla isimden oku (geri uyum)
TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

ADMIN_USER_ID = int(os.getenv("8067876866", "0") or 0)

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN env missing. Set it in Railway Variables."
    )
