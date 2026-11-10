import unittest
from unittest.mock import patch

import sheet_service


class FakeWorksheet:
    def __init__(self, existing=None):
        self.existing = existing
        self.appended_rows = []
        self.find_args = None

    def find(self, value, in_column):
        self.find_args = (value, in_column)
        return self.existing

    def append_row(self, row, value_input_option):
        self.appended_rows.append((row, value_input_option))


class FakeSpreadsheet:
    def __init__(self, worksheet):
        self.sheet1 = worksheet


class FakeClient:
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet

    def open_by_key(self, spreadsheet_id):
        return self.spreadsheet


class SheetServiceTests(unittest.TestCase):
    def setUp(self):
        self.booking = {
            "name": "Alex Rider",
            "phone": "+90 555 123 4567",
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "passengers": 2,
            "date": "2030-01-01 (Tue)",
            "time": "09:00",
        }

    def test_booking_export_appends_row_with_stable_id_column(self):
        worksheet = FakeWorksheet()
        client = FakeClient(FakeSpreadsheet(worksheet))
        with patch.object(sheet_service, "_get_client", return_value=client), patch.object(
            sheet_service, "SPREADSHEET_ID", "sheet-id"
        ):
            sheet_service.append_booking_to_sheet(self.booking, "booking-id")

        self.assertEqual(worksheet.find_args, ("booking-id", 13))
        row, input_option = worksheet.appended_rows[0]
        self.assertEqual(row[-1], "booking-id")
        self.assertEqual(input_option, "RAW")

    def test_booking_export_skips_existing_id(self):
        worksheet = FakeWorksheet(existing=object())
        client = FakeClient(FakeSpreadsheet(worksheet))
        with patch.object(sheet_service, "_get_client", return_value=client), patch.object(
            sheet_service, "SPREADSHEET_ID", "sheet-id"
        ):
            sheet_service.append_booking_to_sheet(self.booking, "booking-id")

        self.assertEqual(worksheet.appended_rows, [])

    def test_booking_export_wraps_expected_service_errors(self):
        with patch.object(sheet_service, "_get_client", side_effect=FileNotFoundError):
            with self.assertRaises(sheet_service.SheetExportError):
                sheet_service.append_booking_to_sheet(self.booking, "booking-id")


if __name__ == "__main__":
    unittest.main()
