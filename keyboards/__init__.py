"""Клавиатуры бота."""

from .inline_admin import get_approve_reject_keyboard
from .main_menu import (
    get_account_status_keyboard,
    get_existing_account_keyboard,
    get_main_menu_keyboard,
    get_new_registration_keyboard,
)

__all__ = (
    "get_approve_reject_keyboard",
    "get_account_status_keyboard",
    "get_existing_account_keyboard",
    "get_main_menu_keyboard",
    "get_new_registration_keyboard",
)
