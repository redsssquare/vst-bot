"""Клавиатуры бота."""

from .inline_admin import get_approve_reject_keyboard
from .main_menu import (
    BTN_BACK,
    BTN_ENTER_ID,
    BTN_ENTER_ID_RECONNECT,
    BTN_GET_ACCESS,
    BTN_I_REGISTERED,
    BTN_NO_REGISTER,
    BTN_RECONNECT,
    BTN_SUPPORT,
    BTN_YES_ACCOUNT,
    get_account_status_keyboard,
    get_await_id_keyboard,
    get_existing_account_keyboard,
    get_main_menu_keyboard,
    get_new_registration_keyboard,
    get_post_id_success_keyboard,
    get_reconnect_instruction_keyboard,
)

__all__ = (
    "BTN_BACK",
    "BTN_ENTER_ID",
    "BTN_ENTER_ID_RECONNECT",
    "BTN_GET_ACCESS",
    "BTN_I_REGISTERED",
    "BTN_NO_REGISTER",
    "BTN_RECONNECT",
    "BTN_SUPPORT",
    "BTN_YES_ACCOUNT",
    "get_approve_reject_keyboard",
    "get_account_status_keyboard",
    "get_await_id_keyboard",
    "get_existing_account_keyboard",
    "get_main_menu_keyboard",
    "get_new_registration_keyboard",
    "get_post_id_success_keyboard",
    "get_reconnect_instruction_keyboard",
)
