import unittest
from collections import defaultdict

from persistence import (
    InvalidStatusTransition,
    PostgresPersistence,
    validate_status_transition,
)


class FakeRepository:
    def __init__(self):
        self.user_data = {123: {"language": "tr"}}
        self.conversations = {}

    def get_user_data(self):
        return defaultdict(dict, self.user_data)

    def update_user_data(self, user_id, data):
        self.user_data[user_id] = data

    def drop_user_data(self, user_id):
        self.user_data.pop(user_id, None)

    def get_conversations(self, name):
        return self.conversations.get(name, {})

    def update_conversation(self, name, key, new_state):
        self.conversations.setdefault(name, {})[key] = new_state


class PostgresPersistenceTests(unittest.IsolatedAsyncioTestCase):
    def test_booking_status_transitions_are_restricted(self):
        validate_status_transition("pending", "confirmed")
        validate_status_transition("confirmed", "cancelled")
        with self.assertRaises(InvalidStatusTransition):
            validate_status_transition("cancelled", "confirmed")
        with self.assertRaises(ValueError):
            validate_status_transition("pending", "unknown")

    async def test_persistence_adapter_restores_and_saves_user_data(self):
        repository = FakeRepository()
        persistence = PostgresPersistence(repository)

        restored = await persistence.get_user_data()
        self.assertEqual(restored[123], {"language": "tr"})

        await persistence.update_user_data(456, {"language": "en"})
        self.assertEqual(repository.user_data[456], {"language": "en"})

    async def test_persistence_adapter_restores_conversation_state(self):
        repository = FakeRepository()
        persistence = PostgresPersistence(repository)

        await persistence.update_conversation("booking", (123, 123), 7)
        restored = await persistence.get_conversations("booking")
        self.assertEqual(restored[(123, 123)], 7)


if __name__ == "__main__":
    unittest.main()
