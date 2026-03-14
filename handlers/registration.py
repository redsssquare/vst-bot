"""Обработчики регистрации — ветки «Нет, зарегистрироваться» и «Да, есть аккаунт»."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, User

import config
import state_manager
from handlers.start import GET_ACCESS_SCREEN_TEXT, START_TEXT
from services import baserow
from keyboards import (
    get_account_status_keyboard,
    get_await_id_keyboard,
    get_existing_account_keyboard,
    get_main_menu_keyboard,
    get_new_registration_keyboard,
    get_post_id_success_keyboard,
    get_reconnect_instruction_keyboard,
)

router = Router(name="registration")


def _format_user_info(from_user: User | None) -> str:
    """Форматирует username для уведомления админу."""
    if not from_user:
        return "Пользователь: Без username"
    return f"Пользователь: @{from_user.username}" if from_user.username else "Пользователь: Без username"


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
    header: str,
    emoji: str,
    action_text: str,
    user_reply: str,
) -> None:
    """Общая логика: уведомление админу, set_step(main), ответ пользователю."""
    user_info = _format_user_info(message.from_user)
    admin_text = (
        f"{emoji} {header}\n\n"
        f"{user_info}\n"
        f"Broker ID: {broker_id}\n\n"
        f"Действие: {action_text}"
    )
    await message.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    user_id = message.from_user.id if message.from_user else 0
    user = await baserow.get_user_by_telegram_id(user_id)
    if user is not None:
        await baserow.update_broker_id(user["id"], broker_id)
    state_manager.set_step(user_id, "main")
    await message.answer(user_reply, reply_markup=get_post_id_success_keyboard())


NO_REGISTER_SCREEN_TEXT = (
    "Чтобы подключиться к системе, зарегистрируйтесь по нашей партнёрской ссылке:\n\n"
    "🔗 {affiliate_link}\n\n"
    "⏱ Регистрация занимает 1–2 минуты.\n\n"
    "Доступ к торговым решениям предоставляется бесплатно.\n\n"
    "⬅️ После регистрации вернитесь в бот и нажмите «✅ Я зарегистрировался»."
)
AWAIT_ID_TEXT = "Отправьте ваш ID аккаунта (числом)."
ID_ERROR_TEXT = "❗ID должен быть числом. Попробуйте ещё раз."
ID_SUBMITTED_TEXT = "✅ ID получен. Мы проверим его и свяжемся с вами."
EXISTING_ACCOUNT_SCREEN_TEXT = (
    "Ваш аккаунт Intrade Bar зарегистрирован по нашей партнёрской ссылке?"
)
SUPPORT_SENT_TEXT = "Сообщение отправлено."

RECONNECT_INSTRUCTION_TEXT = (
    "Если аккаунт уже создан, его можно перевести под нашу партнёрскую ссылку.\n\n"
    "Для этого напишите в поддержку **Intrade Bar**. 👇 Нажмите на текст, чтобы скопировать его.\n\n"
    "```\nЗдравствуйте, переведите меня пожалуйста по партнёрской ссылке\n{affiliate_link}\n```\n\n"
    "После ответа поддержки вернитесь сюда и отправьте ваш ID аккаунта."
)
AWAIT_RECONNECT_ID_TEXT = (
    "Отправьте ваш **ID аккаунта Intrade Bar**.\n"
    "После проверки мы откроем доступ к сигнальной группе."
)


@router.callback_query(F.data == "account:no")
async def handle_no_register(callback: CallbackQuery) -> None:
    """«Нет, зарегистрироваться»: ссылка и клавиатура, остаёмся в choose_account_status."""
    if not callback.from_user or not _step_is_choose_account_status(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    text = NO_REGISTER_SCREEN_TEXT.format(affiliate_link=config.AFFILIATE_LINK)
    await callback.message.answer(text, reply_markup=get_new_registration_keyboard(config.AFFILIATE_LINK))
    user = await baserow.get_user_by_telegram_id(user_id)
    if user is not None:
        await baserow.update_status(user["id"], config.STATUS_WAITING_BROKER_ID, "awaiting_broker_id")
    await callback.answer()


@router.callback_query(F.data == "register:done")
async def handle_registered_click(callback: CallbackQuery) -> None:
    """«Я зарегистрировался»: переводим в ожидание ID."""
    if not callback.from_user or not _step_is_choose_account_status(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "awaiting_new_registration_id")
    await callback.message.answer(AWAIT_ID_TEXT, reply_markup=get_await_id_keyboard())
    await callback.answer()


@router.callback_query(F.data == "account:back")
async def handle_back_from_registration(callback: CallbackQuery) -> None:
    """«Назад» в choose_account_status: возврат в главное меню."""
    if not callback.from_user or not _step_is_choose_account_status(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "main")
    await callback.message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "register:back")
async def handle_back_from_no_register(callback: CallbackQuery) -> None:
    """«Назад» с экрана NO_REGISTER: возврат к choose_account_status (GET_ACCESS)."""
    if not callback.from_user or not _step_is_choose_account_status(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "choose_account_status")
    await callback.message.answer(
        GET_ACCESS_SCREEN_TEXT,
        reply_markup=get_account_status_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(
    F.text,
    lambda m: _step_is_awaiting_new_registration_id(m.from_user.id) if m.from_user else False,
)
async def handle_new_registration_id_input(message: Message) -> None:
    """Обработка ввода ID при state == awaiting_new_registration_id."""
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(ID_ERROR_TEXT)
        return
    await _handle_id_submission(
        message,
        broker_id=raw,
        header="Новая регистрация",
        emoji="🆕",
        action_text="Проверьте ID у брокера и отправьте пользователю доступ.",
        user_reply=ID_SUBMITTED_TEXT,
    )


# --- Ветка «Да, есть аккаунт» ---


@router.callback_query(F.data == "account:yes")
async def handle_yes_existing_account(callback: CallbackQuery) -> None:
    """«Да, есть аккаунт»: текст из ТЗ и клавиатура, state existing_account_options."""
    if not callback.from_user or not _step_is_choose_account_status(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "existing_account_options")
    await callback.message.answer(
        EXISTING_ACCOUNT_SCREEN_TEXT,
        reply_markup=get_existing_account_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "existing:enter_id")
async def handle_enter_id(callback: CallbackQuery) -> None:
    """«Ввести ID»: переводим в awaiting_existing_id."""
    if not callback.from_user or not _step_is_existing_account_options(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "awaiting_existing_id")
    await callback.message.answer(AWAIT_ID_TEXT, reply_markup=get_await_id_keyboard())
    await callback.answer()


@router.callback_query(F.data == "await_id:back")
async def handle_await_id_back(callback: CallbackQuery) -> None:
    """«Назад» из экранов ожидания ID: возврат на нужный экран."""
    if not callback.from_user:
        await callback.answer()
        return
    user_id = callback.from_user.id
    step = state_manager.get_step(user_id)

    if step == "awaiting_new_registration_id":
        state_manager.set_step(user_id, "choose_account_status")
        text = NO_REGISTER_SCREEN_TEXT.format(affiliate_link=config.AFFILIATE_LINK)
        await callback.message.answer(text, reply_markup=get_new_registration_keyboard(config.AFFILIATE_LINK))
    elif step == "awaiting_existing_id":
        if state_manager.get_reconnect_flow(user_id):
            state_manager.set_reconnect_flow(user_id, False)
            state_manager.set_step(user_id, "reconnect_instruction")
            text = RECONNECT_INSTRUCTION_TEXT.format(affiliate_link=config.AFFILIATE_LINK)
            await callback.message.answer(
                text, reply_markup=get_reconnect_instruction_keyboard(config.AFFILIATE_LINK), parse_mode="Markdown"
            )
        else:
            state_manager.set_step(user_id, "existing_account_options")
            await callback.message.answer(
                EXISTING_ACCOUNT_SCREEN_TEXT,
                reply_markup=get_existing_account_keyboard(),
            )
    await callback.answer()


@router.message(
    F.text,
    lambda m: _step_is_awaiting_existing_id(m.from_user.id) if m.from_user else False,
)
async def handle_existing_id_input(message: Message) -> None:
    """Обработка ввода ID при state == awaiting_existing_id."""
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(ID_ERROR_TEXT)
        return
    user_id = message.from_user.id if message.from_user else 0
    if state_manager.get_reconnect_flow(user_id):
        state_manager.set_reconnect_flow(user_id, False)
        await _handle_id_submission(
            message,
            broker_id=raw,
            header="Существующий аккаунт",
            emoji="👤",
            action_text="Проверьте, зарегистрирован ли аккаунт по нашей партнёрской ссылке. Если да — отправьте доступ.",
            user_reply=ID_SUBMITTED_TEXT,
        )
    else:
        await _handle_id_submission(
            message,
            broker_id=raw,
            header="Существующий аккаунт",
            emoji="👤",
            action_text="Проверьте, зарегистрирован ли аккаунт по нашей партнёрской ссылке. Если да — отправьте доступ.",
            user_reply=ID_SUBMITTED_TEXT,
        )


@router.callback_query(F.data == "existing:reconnect")
async def handle_reconnect_request(callback: CallbackQuery) -> None:
    """«Помогите переподключить»: экран 3e — инструкция и inline-кнопки."""
    if not callback.from_user or not _step_is_existing_account_options(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "reconnect_instruction")
    text = RECONNECT_INSTRUCTION_TEXT.format(affiliate_link=config.AFFILIATE_LINK)
    await callback.message.answer(
        text, reply_markup=get_reconnect_instruction_keyboard(config.AFFILIATE_LINK), parse_mode="Markdown"
    )
    user = await baserow.get_user_by_telegram_id(user_id)
    if user is not None:
        await baserow.update_status(user["id"], config.STATUS_WAITING_BROKER_ID, "awaiting_broker_id")
    user_info = _format_user_info(callback.from_user)
    admin_text = (
        "🔁 Запрос на переподключение\n\n"
        f"{user_info}\n\n"
        "Действие: Ожидаем, пока пользователь напишет в поддержку брокера и вернётся с новым Broker ID."
    )
    await callback.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    await callback.answer()


@router.callback_query(F.data == "reconnect:enter_id")
async def handle_reconnect_enter_id(callback: CallbackQuery) -> None:
    """«Ввести ID»: переход в awaiting_existing_id, показ AWAIT_RECONNECT_ID_TEXT."""
    user_id = callback.from_user.id if callback.from_user else 0
    state_manager.set_step(user_id, "awaiting_existing_id")
    state_manager.set_reconnect_flow(user_id, True)
    await callback.message.answer(
        AWAIT_RECONNECT_ID_TEXT, parse_mode="Markdown", reply_markup=get_await_id_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "reconnect:back")
async def handle_reconnect_back(callback: CallbackQuery) -> None:
    """«Назад» из экрана 3e: возврат к existing_account_options."""
    user_id = callback.from_user.id if callback.from_user else 0
    state_manager.set_step(user_id, "existing_account_options")
    await callback.message.answer(
        EXISTING_ACCOUNT_SCREEN_TEXT,
        reply_markup=get_existing_account_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "existing:back")
async def handle_back_from_existing_account(callback: CallbackQuery) -> None:
    """«Назад» из existing_account_options: возврат к «У вас уже есть аккаунт?»."""
    if not callback.from_user or not _step_is_existing_account_options(callback.from_user.id):
        await callback.answer()
        return
    user_id = callback.from_user.id
    state_manager.set_step(user_id, "choose_account_status")
    await callback.message.answer(
        GET_ACCESS_SCREEN_TEXT,
        reply_markup=get_account_status_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# --- Связаться с поддержкой ---


@router.message(
    F.text,
    lambda m: _step_is_awaiting_support_message(m.from_user.id) if m.from_user else False,
)
async def handle_support_message_input(message: Message) -> None:
    """Обработка текста при state == awaiting_support_message: уведомление админу, ответ, main."""
    user_info = _format_user_info(message.from_user)
    text = (message.text or "").strip() or "(пусто)"
    admin_text = (
        "💬 Сообщение от пользователя\n\n"
        f"{user_info}\n\n"
        f"Текст сообщения:\n{text}\n\n"
        "Действие: Ответьте пользователю через Telegram."
    )
    await message.bot.send_message(config.ADMIN_CHAT_ID, admin_text)
    user_id = message.from_user.id if message.from_user else 0
    user = await baserow.get_user_by_telegram_id(user_id)
    if user is not None:
        await baserow.update_status(user["id"], config.STATUS_SUPPORT_MESSAGE, "support_message")
    state_manager.set_step(user_id, "main")
    await message.answer(SUPPORT_SENT_TEXT, reply_markup=get_main_menu_keyboard())


# --- Fallback: текст в состояниях без ожидания ввода ---


@router.message(F.text)
async def handle_text_fallback(message: Message) -> None:
    """Любой необработанный текст: возврат в main с главным меню (Inline)."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")
    await message.answer(START_TEXT, reply_markup=get_main_menu_keyboard())
