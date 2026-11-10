import asyncio
import json
from collections import defaultdict
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from telegram.ext import BasePersistence, PersistenceInput


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql://" + database_url[len("postgres://") :]
    return database_url


class InvalidStatusTransition(ValueError):
    pass


def validate_status_transition(current_status: str, new_status: str) -> None:
    allowed_transitions = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"cancelled"},
        "cancelled": set(),
    }
    if new_status not in allowed_transitions:
        raise ValueError("Unsupported booking status.")
    if new_status != current_status and new_status not in allowed_transitions[current_status]:
        raise InvalidStatusTransition(
            f"Cannot change booking status from {current_status} to {new_status}."
        )


class BookingRepository:
    def __init__(self, database_url: str):
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for PostgreSQL persistence.")
        self.database_url = _normalize_database_url(database_url)

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def initialize(self) -> None:
        with self._connect() as connection:
            for statement in (
                """
                CREATE TABLE IF NOT EXISTS bot_user_data (
                    user_id BIGINT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS bot_conversations (
                    name TEXT NOT NULL,
                    conversation_key TEXT NOT NULL,
                    state JSONB NOT NULL,
                    PRIMARY KEY (name, conversation_key)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id UUID PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed', 'cancelled')),
                    booking_data JSONB NOT NULL,
                    sheet_exported_at TIMESTAMPTZ,
                    sheet_attempts INTEGER NOT NULL DEFAULT 0,
                    sheet_last_error TEXT,
                    next_sheet_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """,
                """
                CREATE INDEX IF NOT EXISTS bookings_created_at_idx
                    ON bookings (created_at DESC)
                """,
                """
                CREATE INDEX IF NOT EXISTS bookings_pending_sheet_idx
                    ON bookings (next_sheet_attempt_at)
                    WHERE sheet_exported_at IS NULL
                """,
            ):
                connection.execute(statement)

    def create_booking(self, user_id: int, booking: dict) -> str:
        booking_id = uuid4()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO bookings (booking_id, user_id, booking_data)
                VALUES (%s, %s, %s)
                """,
                (booking_id, user_id, Jsonb(booking)),
            )
        return str(booking_id)

    def list_bookings(self, limit: int = 20) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT booking_id::text AS booking_id, user_id, status,
                       booking_data, created_at
                FROM bookings
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return rows

    def get_booking(self, booking_id: str) -> dict | None:
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT booking_id::text AS booking_id, user_id, status,
                       booking_data, created_at
                FROM bookings
                WHERE booking_id = %s
                """,
                (UUID(booking_id),),
            ).fetchone()

    def update_booking_status(self, booking_id: str, status: str) -> bool:
        if status not in {"pending", "confirmed", "cancelled"}:
            raise ValueError("Unsupported booking status.")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT status FROM bookings WHERE booking_id = %s FOR UPDATE",
                (UUID(booking_id),),
            ).fetchone()
            if row is None:
                return False
            current_status = row["status"]
            validate_status_transition(current_status, status)
            cursor = connection.execute(
                """
                UPDATE bookings
                SET status = %s, updated_at = NOW()
                WHERE booking_id = %s
                """,
                (status, UUID(booking_id)),
            )
            return cursor.rowcount == 1

    def pending_sheet_exports(self, limit: int = 25) -> list[dict]:
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT booking_id::text AS booking_id, booking_data
                FROM bookings
                WHERE sheet_exported_at IS NULL
                  AND next_sheet_attempt_at <= NOW()
                ORDER BY created_at
                LIMIT %s
                """,
                (limit,),
            ).fetchall()

    def mark_sheet_exported(self, booking_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE bookings
                SET sheet_exported_at = NOW(), sheet_last_error = NULL,
                    updated_at = NOW()
                WHERE booking_id = %s
                """,
                (UUID(booking_id),),
            )

    def mark_sheet_export_failed(self, booking_id: str, error: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE bookings
                SET sheet_attempts = sheet_attempts + 1,
                    sheet_last_error = %s,
                    next_sheet_attempt_at = NOW() + make_interval(
                        secs => LEAST(
                            3600,
                            (30 * power(2::numeric, LEAST(sheet_attempts, 7)))::integer
                        )
                    ),
                    updated_at = NOW()
                WHERE booking_id = %s
                """,
                (error[:500], UUID(booking_id)),
            )

    def get_user_data(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT user_id, data FROM bot_user_data"
            ).fetchall()
        return defaultdict(dict, {row["user_id"]: row["data"] for row in rows})

    def update_user_data(self, user_id: int, data: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO bot_user_data (user_id, data)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data
                """,
                (user_id, Jsonb(dict(data))),
            )

    def drop_user_data(self, user_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM bot_user_data WHERE user_id = %s", (user_id,)
            )

    def get_conversations(self, name: str) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT conversation_key, state
                FROM bot_conversations
                WHERE name = %s
                """,
                (name,),
            ).fetchall()
        conversations = {}
        for row in rows:
            key = json.loads(row["conversation_key"])
            conversations[tuple(key) if isinstance(key, list) else key] = row["state"]
        return conversations

    def update_conversation(self, name: str, key, new_state) -> None:
        conversation_key = json.dumps(key)
        with self._connect() as connection:
            if new_state is None:
                connection.execute(
                    """
                    DELETE FROM bot_conversations
                    WHERE name = %s AND conversation_key = %s
                    """,
                    (name, conversation_key),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO bot_conversations (name, conversation_key, state)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name, conversation_key)
                    DO UPDATE SET state = EXCLUDED.state
                    """,
                    (name, conversation_key, Jsonb(new_state)),
                )


class PostgresPersistence(BasePersistence):
    def __init__(self, repository: BookingRepository):
        super().__init__(
            store_data=PersistenceInput(
                user_data=True,
                chat_data=False,
                bot_data=False,
                callback_data=False,
            ),
            update_interval=10,
        )
        self.repository = repository

    async def get_user_data(self):
        return await asyncio.to_thread(self.repository.get_user_data)

    async def update_user_data(self, user_id, data):
        await asyncio.to_thread(self.repository.update_user_data, user_id, data)

    async def drop_user_data(self, user_id):
        await asyncio.to_thread(self.repository.drop_user_data, user_id)

    async def get_chat_data(self):
        return defaultdict(dict)

    async def update_chat_data(self, chat_id, data):
        return None

    async def drop_chat_data(self, chat_id):
        return None

    async def get_bot_data(self):
        return {}

    async def update_bot_data(self, data):
        return None

    async def get_callback_data(self):
        return None

    async def update_callback_data(self, data):
        return None

    async def get_conversations(self, name):
        return await asyncio.to_thread(self.repository.get_conversations, name)

    async def update_conversation(self, name, key, new_state):
        await asyncio.to_thread(
            self.repository.update_conversation, name, key, new_state
        )

    async def refresh_user_data(self, user_id, user_data):
        return None

    async def refresh_chat_data(self, chat_id, chat_data):
        return None

    async def refresh_bot_data(self, bot_data):
        return None

    async def flush(self):
        return None
