# config.py
import os
from dotenv import load_dotenv
from utils.environment import parse_admin_user_id

# Lokal geliştirme için .env desteği (Railway'de etkisi olmaz ama lokal güzel olur)
load_dotenv()

# Birden fazla isimden oku (geri uyum)
TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN env missing. Set it in Railway Variables."
    )

try:
    ADMIN_USER_ID = parse_admin_user_id(os.getenv("ADMIN_USER_ID"))
except ValueError as exc:
    raise RuntimeError(str(exc)) from exc

DATABASE_URL = os.getenv("DATABASE_URL")
