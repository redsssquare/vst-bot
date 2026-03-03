"""Обработчики регистрации — ветки «Нет, зарегистрироваться» и «Да, есть аккаунт»."""

from aiogram import F, Router
from aiogram.types import Message

import config
import state_manager
from handlers.start import START_TEXT
from keyboards import (
    get_account_status_keyboard,
    get_existing_account_keyboard,
    get_main_menu_keyboard,
    get_new_registration_keyboard,
)

router = Router(name="registration")


def _format_user_info(message: Message) -> str:
    """Форматирует Username и Telegram ID для уведомления админу."""
    if not message.from_user:
        return "Telegram ID: —"
    user_id = message.from_user.id
    username = message.from_user.username
    user_display = f"@{username}" if username else "(нет)"
    return f"Username: {user_display}\nTelegram ID: {user_id}"


def _step_is_choose_account_status(user_id: int) -> bool:
    return state_manager.get_step(user_id) == "choose_account_status"


def _step_is_awaiting_new_registration_id(user_id: int) -> bool:
    return state_manager.get_step(user_id) == "awaiting_new_registration_id"


def _step_is_existing_account_options(user_id: int) -> bool:
    return state_manager.get_step(user_id) == "existing_account_options"


def _step_is_awaiting_existing_id(user_id: int) -> bool:
    return state_manager.get_step(user_id) == "awaiting_existing_id"


def _step_is_awaiting_support_message(user_id: int) -> bool:
    return state_manager.get_step(user_id) == "awaiting_support_message"


async def _handle_id_submission(
    message: Message,
    broker_id: str,
    admin_header: str,
    admin_type: str,
    user_reply: str,
) -> None:
    """Общая логика: уведомление админу, set_step(main), ответ пользователю."""
    user_info = _format_user_info(message)
    admin_text = f"{admin_header}\n{user_info}\nBroker ID: {broker_id}\nТип: {admin_type}"
    await message.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer(user_reply, reply_markup=get_main_menu_keyboard())


@router.message(
    F.text.casefold() == "нет, зарегистрироваться",
    lambda m: _step_is_choose_account_status(m.from_user.id) if m.from_user else False,
)
async def handle_no_register(message: Message) -> None:
    """«Нет, зарегистрироваться»: ссылка и клавиатура, остаёмся в choose_account_status."""
    link = config.AFFILIATE_LINK
    text = (
        f"Зарегистрируйтесь по партнёрской ссылке:\n{link}\n\n"
        "После регистрации нажмите кнопку ниже."
    )
    await message.answer(text, reply_markup=get_new_registration_keyboard())


@router.message(
    F.text.casefold() == "я зарегистрировался",
    lambda m: _step_is_choose_account_status(m.from_user.id) if m.from_user else False,
)
async def handle_registered_click(message: Message) -> None:
    """«Я зарегистрировался»: переводим в ожидание ID."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "awaiting_new_registration_id")
    await message.answer("Отправьте ваш ID аккаунта (числом).")


@router.message(
    F.text.casefold() == "назад",
    lambda m: _step_is_choose_account_status(m.from_user.id) if m.from_user else False,
)
async def handle_back_from_registration(message: Message) -> None:
    """«Назад» в choose_account_status: возврат в главное меню."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(
    F.text,
    lambda m: _step_is_awaiting_new_registration_id(m.from_user.id) if m.from_user else False,
)
async def handle_new_registration_id_input(message: Message) -> None:
    """Обработка ввода ID при state == awaiting_new_registration_id."""
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("ID должен быть числом. Попробуйте ещё раз.")
        return
    await _handle_id_submission(
        message,
        broker_id=raw,
        admin_header="Новая регистрация",
        admin_type="Новая регистрация",
        user_reply="ID получен. Ожидайте проверки.",
    )


# --- Ветка «Да, есть аккаунт» ---


@router.message(
    F.text.casefold() == "да, есть аккаунт",
    lambda m: _step_is_choose_account_status(m.from_user.id) if m.from_user else False,
)
async def handle_yes_existing_account(message: Message) -> None:
    """«Да, есть аккаунт»: текст из ТЗ и клавиатура, state existing_account_options."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "existing_account_options")
    text = (
        "Если аккаунт зарегистрирован по нашей ссылке — отправьте ID. "
        "Если нет — мы поможем переподключить его за несколько минут."
    )
    await message.answer(text, reply_markup=get_existing_account_keyboard())


@router.message(
    F.text.casefold() == "ввести id",
    lambda m: _step_is_existing_account_options(m.from_user.id) if m.from_user else False,
)
async def handle_enter_id(message: Message) -> None:
    """«Ввести ID»: переводим в awaiting_existing_id."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "awaiting_existing_id")
    await message.answer("Отправьте ваш ID аккаунта (числом).")


@router.message(
    F.text.casefold() == "назад",
    lambda m: _step_is_awaiting_existing_id(m.from_user.id) if m.from_user else False,
)
async def handle_back_from_awaiting_existing_id(message: Message) -> None:
    """«Назад» из awaiting_existing_id: возврат к экрану «Ввести ID / Помогите»."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "existing_account_options")
    text = (
        "Если аккаунт зарегистрирован по нашей ссылке — отправьте ID. "
        "Если нет — мы поможем переподключить его за несколько минут."
    )
    await message.answer(text, reply_markup=get_existing_account_keyboard())


@router.message(
    F.text,
    lambda m: _step_is_awaiting_existing_id(m.from_user.id) if m.from_user else False,
)
async def handle_existing_id_input(message: Message) -> None:
    """Обработка ввода ID при state == awaiting_existing_id."""
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("ID должен быть числом. Попробуйте ещё раз.")
        return
    await _handle_id_submission(
        message,
        broker_id=raw,
        admin_header="Пользователь с уже существующим аккаунтом",
        admin_type="Уже был аккаунт",
        user_reply="ID получен. Ожидайте проверки.",
    )


@router.message(
    F.text.casefold() == "помогите переподключить",
    lambda m: _step_is_existing_account_options(m.from_user.id) if m.from_user else False,
)
async def handle_reconnect_request(message: Message) -> None:
    """«Помогите переподключить»: уведомление админу, ответ, main."""
    user_info = _format_user_info(message)
    admin_text = f"Запрос на переподключение аккаунта\n{user_info}"
    await message.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer(
        "Запрос отправлен. Мы свяжемся с вами.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(
    F.text.casefold() == "назад",
    lambda m: _step_is_existing_account_options(m.from_user.id) if m.from_user else False,
)
async def handle_back_from_existing_account(message: Message) -> None:
    """«Назад» из existing_account_options: возврат к «У вас уже есть аккаунт?»."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "choose_account_status")
    await message.answer(
        "У вас уже есть аккаунт в InTradeBar?",
        reply_markup=get_account_status_keyboard(),
    )


# --- Связаться с поддержкой ---


@router.message(
    F.text,
    lambda m: _step_is_awaiting_support_message(m.from_user.id) if m.from_user else False,
)
async def handle_support_message_input(message: Message) -> None:
    """Обработка текста при state == awaiting_support_message: уведомление админу, ответ, main."""
    user_info = _format_user_info(message)
    text = (message.text or "").strip() or "(пусто)"
    admin_text = f"Сообщение в поддержку\n{user_info}\nТекст: {text}"
    await message.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer("Сообщение отправлено.", reply_markup=get_main_menu_keyboard())


# --- Fallback: текст в состояниях без ожидания ввода ---


@router.message(F.text)
async def handle_text_fallback(message: Message) -> None:
    """Любой необработанный текст: возврат в main с главным меню."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer(START_TEXT, reply_markup=get_main_menu_keyboard())
