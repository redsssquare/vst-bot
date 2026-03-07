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


def set_crm_write_target(user_id: int, target_telegram_id: int) -> None:
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_write_target"] = target_telegram_id


def get_crm_write_target(user_id: int) -> int | None:
    return _storage.get(user_id, {}).get("crm_write_target")


def clear_crm_write_target(user_id: int) -> None:
    if user_id in _storage:
        _storage[user_id].pop("crm_write_target", None)


def set_crm_list_source(user_id: int, source: str) -> None:
    """Сохранить источник списка: waiting, new, support, all."""
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_list_source"] = source


def get_crm_list_source(user_id: int) -> str | None:
    """Получить источник списка для возврата из карточки."""
    return _storage.get(user_id, {}).get("crm_list_source")


def set_crm_list_page(user_id: int, page: int) -> None:
    """Сохранить текущую страницу списка для возврата из карточки."""
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_list_page"] = page


def get_crm_list_page(user_id: int) -> int:
    """Получить страницу списка для возврата из карточки."""
    return _storage.get(user_id, {}).get("crm_list_page", 0)


def set_crm_list_users(user_id: int, users: list) -> None:
    """Сохранить список пользователей текущей страницы (для «Следующий лид»)."""
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_list_users"] = users


def get_crm_list_users(user_id: int) -> list | None:
    """Получить сохранённый список пользователей текущей страницы."""
    return _storage.get(user_id, {}).get("crm_list_users")


def set_crm_list_user_index(user_id: int, index: int) -> None:
    """Сохранить индекс пользователя в текущей странице (0–9)."""
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_list_user_index"] = index


def get_crm_list_user_index(user_id: int) -> int | None:
    """Получить индекс пользователя в текущей странице."""
    return _storage.get(user_id, {}).get("crm_list_user_index")


def set_crm_list_total(user_id: int, total: int) -> None:
    """Сохранить общее количество пользователей в списке."""
    if user_id not in _storage:
        _storage[user_id] = {}
    _storage[user_id]["crm_list_total"] = total


def get_crm_list_total(user_id: int) -> int | None:
    """Получить общее количество пользователей в списке."""
    return _storage.get(user_id, {}).get("crm_list_total")
