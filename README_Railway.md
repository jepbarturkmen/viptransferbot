# Railway Deployment Notes

## Start Command
- `python vip_bot_fix20/vip_bot/main.py`

## Env Vars (set in Railway → Variables)
- `TOKEN` : your Telegram bot token
- `ADMIN_USER_ID` : numeric Telegram user id for admin
- (optional) `TZ=Asia/Bangkok`
- (optional) `NIXPACKS_PYTHON_VERSION=3.11`

## Service Type
- Worker (not Web)

## Requirements
A `requirements.txt` must be present in the repo root.
