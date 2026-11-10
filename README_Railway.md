# Railway Deployment Notes

## Start Command
- `python main.py`

## Env Vars (set in Railway → Variables)
- `TELEGRAM_BOT_TOKEN` : your Telegram bot token (`TOKEN` is also accepted for compatibility)
- `ADMIN_USER_ID` : numeric Telegram user id for admin
- `DATABASE_URL` : Railway PostgreSQL connection URL (required for persistent bookings and conversation state)
- `GOOGLE_APPLICATION_CREDENTIALS` : path to the service-account JSON file (or configure credentials using your deployment's secret mechanism)
- `SHEETS_SPREADSHEET_ID` : Google Sheet ID (recommended; alternatively set `SHEETS_SPREADSHEET_NAME`)
- `LOG_LEVEL` : optional Python log level (`INFO` by default)
- (optional) `TZ=Asia/Bangkok`
- (optional) `NIXPACKS_PYTHON_VERSION=3.11`

`ADMIN_USER_ID` must be a positive numeric Telegram user ID. PostgreSQL is the source of truth for bookings and user/conversation state. When a booking is saved, its Google Sheets export is queued and retried if Google is temporarily unavailable.
Create/link a Railway PostgreSQL service and expose its connection URL as `DATABASE_URL`. Database tables are initialized at startup. Existing Google Sheets rows are left as-is and are not imported into PostgreSQL.
Do not commit bot tokens, database URLs, or Google service-account credentials.

## Admin commands
- `/bookings` — list the 15 most recent bookings
- `/booking <booking-id>` — view a booking
- `/booking_status <booking-id> <pending|confirmed|cancelled>` — update its status

Only the configured `ADMIN_USER_ID` can use these commands.
Bookings start as `pending`; admins can move them to `confirmed` or `cancelled`. Confirmed bookings can be cancelled, and cancelled bookings cannot be reopened through the bot.

## Service Type
- Worker (not Web)

## Requirements
A `requirements.txt` must be present in the repo root.
