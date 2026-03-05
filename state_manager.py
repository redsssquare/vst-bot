"""In-memory state manager for user data."""

_storage: dict[int, dict] = {}


def set_step(user_id: int, step: str) -> None:
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["step"] = step


def get_step(user_id: int) -> str | None:
    return _storage.get(user_id, {}).get("step")


def set_broker_id(user_id: int, broker_id: str) -> None:
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["broker_id"] = broker_id


def get_user(user_id: int) -> dict | None:
    return _storage.get(user_id)


def clear_user(user_id: int) -> None:
    _storage.pop(user_id, None)


def set_reconnect_flow(user_id: int, value: bool) -> None:
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["reconnect_flow"] = value


def get_reconnect_flow(user_id: int) -> bool:
    return _storage.get(user_id, {}).get("reconnect_flow", False)
