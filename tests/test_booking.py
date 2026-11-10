import unittest
from datetime import date, timedelta

from utils.booking import build_sheet_row, validate_booking
from utils.environment import parse_admin_user_id
from utils.state import reset_booking


class BookingHelpersTests(unittest.TestCase):
    def setUp(self):
        self.booking = {
            "name": "Alex Rider",
            "phone": "+90 555 123 4567",
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "passengers": 3,
            "baby_seat": "no",
            "notes": "",
            "date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d (%a)"),
            "time": "09:30",
            "flight_number": "TK123",
            "meeting_time": "08:30",
            "telegram_user_id": 12345,
        }

    def test_build_sheet_row_preserves_legacy_columns_and_adds_booking_id(self):
        self.assertEqual(
            build_sheet_row(self.booking, "booking-123"),
            [
                "Alex Rider",
                "+90 555 123 4567",
                "Airport",
                "Hotel",
                3,
                "no",
                "",
                self.booking["date"],
                "09:30",
                "TK123",
                "08:30",
                "12345",
                "booking-123",
            ],
        )

    def test_validate_booking_accepts_valid_booking(self):
        validate_booking(self.booking)

    def test_validate_booking_rejects_invalid_phone_and_time(self):
        invalid_phone = {**self.booking, "phone": "call me"}
        invalid_time = {**self.booking, "time": "25:99"}
        with self.assertRaises(ValueError):
            validate_booking(invalid_phone)
        with self.assertRaises(ValueError):
            validate_booking(invalid_time)

    def test_validate_booking_rejects_past_date(self):
        booking = {**self.booking, "date": "2000-01-01 (Sat)"}
        with self.assertRaises(ValueError):
            validate_booking(booking)

    def test_validate_booking_rejects_dates_outside_picker_range(self):
        booking = {
            **self.booking,
            "date": (date.today() + timedelta(days=90)).strftime("%Y-%m-%d (%a)"),
        }
        with self.assertRaises(ValueError):
            validate_booking(booking)

    def test_parse_admin_user_id_requires_positive_integer(self):
        self.assertEqual(parse_admin_user_id("8067876866"), 8067876866)
        for value in (None, "", "admin", "0", "-2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_admin_user_id(value)

    def test_reset_booking_keeps_language_and_unrelated_user_data(self):
        user_data = {
            "language": "tr",
            "name": "Alex Rider",
            "pickup_location": "Airport",
            "custom_setting": True,
        }
        reset_booking(user_data)
        self.assertEqual(user_data, {"language": "tr", "custom_setting": True})


if __name__ == "__main__":
    unittest.main()
