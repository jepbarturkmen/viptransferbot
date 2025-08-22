# config.py (güvenli sürüm)
import os

# .env yerine Railway Variables kullanacaksın
TOKEN = os.getenv("7969003527:AAEv7GWVE_u7Ddh4xT4bwNVoJfHZnq7h4OU")  # ENV adı standardize ettik
ADMIN_USER_ID = int(os.getenv("8067876866", "0") or 0)

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN env missing. Set it in Railway Variables.")
