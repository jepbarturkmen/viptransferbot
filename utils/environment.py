def parse_admin_user_id(value: str | None) -> int:
    if value is None or not value.strip():
        raise ValueError("ADMIN_USER_ID is required.")
    try:
        user_id = int(value.strip())
    except ValueError as exc:
        raise ValueError("ADMIN_USER_ID must be a positive integer.") from exc
    if user_id <= 0:
        raise ValueError("ADMIN_USER_ID must be a positive integer.")
    return user_id
