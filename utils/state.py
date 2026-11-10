BOOKING_FIELDS = (
    "pickup_category",
    "dropoff_category",
    "pickup_location",
    "dropoff_location",
    "passengers",
    "date",
    "time",
    "flight_number",
    "meeting_time",
    "name",
    "phone",
    "baby_seat",
    "notes",
)


def reset_booking(user_data: dict) -> None:
    for field in BOOKING_FIELDS:
        user_data.pop(field, None)