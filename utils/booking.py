import re
from datetime import date, datetime, timedelta


def build_sheet_row(booking: dict, booking_id: str) -> list:
    return [
        booking.get("name", ""),
        booking.get("phone", ""),
        booking.get("pickup_location", ""),
        booking.get("dropoff_location", ""),
        booking.get("passengers", ""),
        booking.get("baby_seat", ""),
        booking.get("notes", ""),
        booking.get("date", ""),
        booking.get("time", ""),
        booking.get("flight_number", ""),
        booking.get("meeting_time", ""),
        str(booking.get("telegram_user_id", "")),
        booking_id,
    ]


def validate_booking(booking: dict) -> None:
    required = (
        "name",
        "phone",
        "pickup_location",
        "dropoff_location",
        "passengers",
        "date",
        "time",
    )
    if any(not str(booking.get(field, "")).strip() for field in required):
        raise ValueError("A required booking field is missing.")
    if any(
        len(str(booking[field]).strip()) > 300
        for field in ("pickup_location", "dropoff_location")
    ):
        raise ValueError("Booking locations must be 300 characters or fewer.")
    if len(str(booking.get("notes", ""))) > 1000:
        raise ValueError("Extra requests must be 1000 characters or fewer.")
    if len(str(booking.get("flight_number", ""))) > 30:
        raise ValueError("Flight number must be 30 characters or fewer.")

    name = str(booking["name"]).strip()
    if len(name) < 2 or len(name) > 100:
        raise ValueError("Enter a name between 2 and 100 characters.")

    phone = str(booking["phone"]).strip()
    digits = re.sub(r"\D", "", phone)
    if not re.fullmatch(r"\+?[0-9\s().-]{7,24}", phone) or not 7 <= len(digits) <= 15:
        raise ValueError("Enter a valid phone number with country code.")

    if booking["passengers"] not in (1, 2, 3, 4, 5, "5-15", "15+"):
        raise ValueError("Choose a valid passenger count.")

    date_text = str(booking["date"])
    try:
        booking_date = datetime.strptime(date_text, "%Y-%m-%d (%a)").date()
    except ValueError as exc:
        raise ValueError("Choose a valid booking date.") from exc
    today = date.today()
    if not today <= booking_date <= today + timedelta(days=89):
        raise ValueError("Choose a date within the available booking calendar.")

    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(booking["time"])):
        raise ValueError("Choose a valid booking time.")
