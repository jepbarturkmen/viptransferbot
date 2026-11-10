import os
import gspread
import requests
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException

from utils.booking import build_sheet_row

# Scopes for Sheets & Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Credentials file path (prefer env var; fallback to ./credentials/credentials.json)
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.path.join(
    os.path.dirname(__file__), "credentials", "credentials.json"
)

# Spreadsheet identification: prefer ID from env/config; fallback to name
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SPREADSHEET_NAME = os.getenv("SHEETS_SPREADSHEET_NAME", "VIP Transfer Bookings")

_client = None


class SheetExportError(Exception):
    """A recoverable error while exporting a booking to Google Sheets."""


def _get_client():
    global _client
    if _client is None:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account JSON not found: {SERVICE_ACCOUNT_FILE}")
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client

def append_to_sheet(row):
    """
    Append one row to the spreadsheet's first worksheet.
    Row: list of primitive values (strings/numbers).
    """
    client = _get_client()
    if SPREADSHEET_ID:
        sh = client.open_by_key(SPREADSHEET_ID)
    else:
        # Fallback to spreadsheet name
        sh = client.open(SPREADSHEET_NAME)
    ws = sh.sheet1
    ws.append_row(row, value_input_option="RAW")
    return True


def append_booking_to_sheet(booking, booking_id):
    try:
        client = _get_client()
        if SPREADSHEET_ID:
            sh = client.open_by_key(SPREADSHEET_ID)
        else:
            sh = client.open(SPREADSHEET_NAME)
        ws = sh.sheet1
        if ws.find(booking_id, in_column=13) is None:
            ws.append_row(
                build_sheet_row(booking, booking_id),
                value_input_option="RAW",
            )
        return True
    except (FileNotFoundError, OSError, GoogleAuthError, GSpreadException, requests.RequestException) as exc:
        raise SheetExportError("Google Sheets export is unavailable.") from exc
