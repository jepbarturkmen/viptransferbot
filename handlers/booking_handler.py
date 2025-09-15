from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.pickup_location_handler import ask_pickup_type, ask_pickup_location, receive_pickup_location
from handlers.dropoff_location_handler import (
    ask_dropoff_type, ask_dropoff_location, receive_dropoff_location,
    receive_passenger_count, ask_date, receive_date, back_to_date, receive_time
)
from handlers.passenger_info_handler import (
    ask_name, receive_name, ask_phone, receive_phone,
    ask_baby_seat, receive_baby_seat, receive_notes, receive_notes_skip
)
from handlers.confirm_handler import confirm_booking, cancel_booking
from handlers.extra_info_handler import (
    ask_flight_number_if_airport, receive_flight_number,
    ask_meeting_time, receive_meeting_time,
)
from handlers.states import (
    ASK_PICKUP_TYPE,
    WAITING_PICKUP_CATEGORY,
    WAITING_PICKUP_LOCATION,
    ASK_DROPOFF_TYPE,
    WAITING_DROPOFF_CATEGORY,
    WAITING_DROPOFF_LOCATION,
    ASK_DATE,
    WAITING_DATE,
    ASK_TIME,
    WAITING_TIME,
    ASK_PASSENGER_COUNT,
    WAITING_NAME,
    WAITING_PHONE,
    ASK_BABY_SEAT,
    WAITING_BABY_SEAT,
    WAITING_NOTES,
    SHOW_SUMMARY,
    WAITING_CONFIRMATION,
    ASK_FLIGHT_NUMBER,
    WAITING_FLIGHT_NUMBER,
    ASK_MEETING_TIME,
    WAITING_MEETING_TIME,

)

async def _end_to_menu(update, context):
    if update.callback_query:
        await update.callback_query.answer()
    return ConversationHandler.END

booking_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_pickup_type, pattern=r'^new_booking$')],
    states={
        # choose pickup category (airport/hotel/custom)
        ASK_PICKUP_TYPE: [
            CallbackQueryHandler(ask_pickup_location, pattern=r'^(pickup_airport|pickup_hotel|pickup_aratransfer)$')
        ],
        # legacy/alias state (safe no-op): route to same handler
        WAITING_PICKUP_CATEGORY: [
            CallbackQueryHandler(ask_pickup_location, pattern=r'^(pickup_airport|pickup_hotel|pickup_aratransfer)$')
        ],
        # choose pickup location or type an address; also allow going back
        WAITING_PICKUP_LOCATION: [
            CallbackQueryHandler(receive_pickup_location, pattern=r'^(pickup_loc_|pickup_type_back$)'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pickup_location),
        ],

        # after pickup is saved, we call ask_dropoff_type() directly -> WAITING_DROPOFF_CATEGORY
        WAITING_DROPOFF_CATEGORY: [
            CallbackQueryHandler(ask_dropoff_location, pattern=r'^(dropoff_category_airport|dropoff_category_hotel|dropoff_category_custom)$')
        ],
        WAITING_DROPOFF_LOCATION: [
            CallbackQueryHandler(receive_dropoff_location, pattern=r'^dropoff_loc:'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dropoff_location),
        ],

        # date/time pickers
        WAITING_DATE: [
            CallbackQueryHandler(receive_date, pattern=r'^date_'),
        ],
        WAITING_TIME: [
            CallbackQueryHandler(receive_time, pattern=r'^time_'),
            CallbackQueryHandler(back_to_date, pattern=r'^back_to_date$'),
        ],
        ASK_FLIGHT_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_flight_number),
            CallbackQueryHandler(receive_flight_number, pattern=r'^(flight_skip)$'),
        ],
        WAITING_FLIGHT_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_flight_number),
            CallbackQueryHandler(receive_flight_number, pattern=r'^(flight_skip)$'),
        ],
        ASK_MEETING_TIME: [
            CallbackQueryHandler(receive_meeting_time, pattern=r'^(meet_|meet_skip)')
        ],
        WAITING_MEETING_TIME: [
            CallbackQueryHandler(receive_meeting_time, pattern=r'^(meet_|meet_skip)')
        ],

        # pax → personal info
        ASK_PASSENGER_COUNT: [
            CallbackQueryHandler(receive_passenger_count, pattern=r'^pax_')
        ],
        WAITING_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
        ],
        WAITING_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
        ],
        WAITING_BABY_SEAT: [
            CallbackQueryHandler(receive_baby_seat, pattern=r'^(baby_yes|baby_no)$')
        ],
        WAITING_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_notes),
            CallbackQueryHandler(receive_notes_skip, pattern=r'^notes_skip$'),
        ],
        SHOW_SUMMARY: [
            CallbackQueryHandler(confirm_booking, pattern=r'^confirm_booking$'),
            CallbackQueryHandler(cancel_booking, pattern=r'^cancel_booking$'),
        ],
        WAITING_CONFIRMATION: [
            CallbackQueryHandler(confirm_booking, pattern=r'^confirm_booking$'),
            CallbackQueryHandler(cancel_booking, pattern=r'^cancel_booking$'),
        ],
    },
    fallbacks=[CallbackQueryHandler(_end_to_menu, pattern=r'^back_to_menu$')],
    allow_reentry=True,
)
