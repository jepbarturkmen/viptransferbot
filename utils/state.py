# utils/state.py

class UserState:
    _states = {}

    @classmethod
    def get(cls, user_id: int):
        return cls._states.get(user_id, {})

    @classmethod
    def set(cls, user_id: int, key: str, value):
        if user_id not in cls._states or not isinstance(cls._states[user_id], dict):
            cls._states[user_id] = {}
        cls._states[user_id][key] = value

    @classmethod
    def clear(cls, user_id: int):
        if user_id in cls._states:
            del cls._states[user_id]


def reset_booking(user_id: int):
    """Clear current booking fields for a fresh start."""
    try:
        # Use UserState API to avoid NameError and keep internal structure intact
        from utils.state import UserState  # local import safe inside same module context
    except Exception:
        pass
    try:
        UserState.set(user_id, "pickup_location", None)
        UserState.set(user_id, "dropoff_location", None)
        UserState.set(user_id, "passengers", None)
    except Exception:
        # Fallback: attempt to mutate internal storage if available
        st = {}
        try:
            st = UserState.get(user_id)
        except Exception:
            pass
        if isinstance(st, dict):
            st.update({
                "pickup_location": None,
                "dropoff_location": None,
                "passengers": None,
            })
    