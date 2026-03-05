# Changelog

## [Unreleased]

### UX text polishing

- **START_TEXT**: emojis 📍 📊 🔄, improved formatting.
- **Main menu buttons**: 🚀 Получить доступ, 💬 Поддержка (was: 🔓 Получить доступ, 💬 Связаться с поддержкой).
- **GET_ACCESS_SCREEN_TEXT**: **Intrade Bar** (Markdown), ⚙️ before algorithm line.
- **NO_REGISTER_SCREEN_TEXT**: 🔗 before affiliate link.
- **RECONNECT_INSTRUCTION_TEXT**: ☝️ before copy hint, code block for support message template.
- **ID_SUBMITTED_TEXT**: ✅ prefix.
- **docs/TEXTS_FUNNEL.md**: updated with new texts and button labels.

### Stage 3: UX Inline Buttons — документация и проверка

- **docs/TEXTS_FUNNEL.md**: уточнено, что используются только Inline-кнопки; добавлена таблица callback_data (keyboards → handlers); обновлена таблица навигации «Назад»; уточнён экран 3d (два варианта текста: AWAIT_ID_TEXT / AWAIT_RECONNECT_ID_TEXT).
- Проверка: callback_data уникальны (main:, account:, register:, existing:, reconnect:, await_id:); все переходы «Назад» корректны.

### Stage 2: Text updates

- **handlers/start.py**: `START_TEXT` shortened; `GET_ACCESS_SCREEN_TEXT` simplified.
- **handlers/registration.py**: `NO_REGISTER_SCREEN_TEXT`, `RECONNECT_INSTRUCTION_TEXT`, `ID_SUBMITTED_TEXT` updated.
- После отправки ID главное меню не показывается (только текст подтверждения).
- **docs/TEXTS_FUNNEL.md**: обновлены тексты по этапам воронки.

### Stage 1: Inline keyboards migration

- **keyboards/main_menu.py**, **keyboards/__init__.py**: все ReplyKeyboard заменены на InlineKeyboard; добавлен `get_await_id_keyboard()` для экранов ожидания ID (3b, 3d).
- **handlers/start.py**, **handlers/registration.py**: обработчики кнопок переведены с `F.text` на `callback_query`.
- Экран 3e (переподключение): кнопка «Скопировать текст» удалена.

### Stage 1: Screen 3e — Запрос на переподключение

- **handlers/registration.py**: шаг `reconnect_instruction`; константы `RECONNECT_INSTRUCTION_TEXT`, `AWAIT_RECONNECT_ID_TEXT`; inline-клавиатура «Ввести ID», «Назад»; возврат на «Есть аккаунт» из 3e; возврат на 3e из «Ввести ID» при переходе из 3e.
- **docs/TEXTS_FUNNEL.md**: обновлён раздел 3e, правила навигации «Назад», сводка констант.
- Удалена константа `RECONNECT_SENT_TEXT`.

### Stage 1: Контент и кнопки MVP (Content MVP Bot plan)

- **keyboards/main_menu.py**: 8 button constants (BTN_*) with emoji; all keyboard builders use them.
- **keyboards/__init__.py**: re-exports the 8 BTN_* constants from main_menu for handlers.
- **handlers/start.py**: START_TEXT, GET_ACCESS_SCREEN_TEXT, SUPPORT_WAIT_TEXT; button filters use keyboard constants (F.text == BTN_*).
- **handlers/registration.py**: all screen text constants; all button filters use keyboard constants; cross-import of GET_ACCESS_SCREEN_TEXT from start.
- Content/buttons MVP complete: funnel texts and buttons use short, structured wording and emoji; button labels centralized in keyboards.

### Stage 7: Очистка и интеграция — MVP funnel complete

- **Removed**: `handlers/admin.py` (approve/reject callbacks)
- **handlers/__init__.py**: `admin_router` removed from exports
- **app.py**: `admin_router` removed from `dp.include_router`
- MVP funnel complete

### Added — Stage 6: Handlers — поддержка и fallback

- **handlers/registration.py**: `handle_support_message_input` — при state `awaiting_support_message` любой текст → уведомление в `ADMIN_CHAT_ID`, `set_step(main)`, ответ пользователю
- `handle_text_fallback` — любой необработанный текст → возврат в `main` с главным меню (`START_TEXT`, `get_main_menu_keyboard`)

### Added — Stage 5: Handlers — ветка «Да, есть аккаунт»

- **handlers/registration.py**: ветка «Да, есть аккаунт» — `handle_yes_existing_account` → state `existing_account_options`, `get_existing_account_keyboard`
- «Ввести ID» → `set_step(awaiting_existing_id)`; «Помогите переподключить» → уведомление в `ADMIN_CHAT_ID`, `set_step(main)`; «Назад» (из `existing_account_options` и `awaiting_existing_id`)
- `_handle_id_submission` — общая логика для обоих типов ID (новая регистрация / уже есть аккаунт): уведомление в `ADMIN_CHAT_ID`, `set_step(main)`, ответ пользователю
- Оба типа уведомлений («Новая регистрация», «Уже был аккаунт», «Запрос на переподключение») отправляются в `ADMIN_CHAT_ID`

### Added — Stage 4: Handlers — ветка «Нет, зарегистрироваться»

- **handlers/registration.py**: `registration_router` — ветка «Нет, зарегистрироваться» (affiliate link + `get_new_registration_keyboard`); «Я зарегистрировался» → `set_step(awaiting_new_registration_id)`; «Назад» → main menu
- `handle_new_registration_id_input`: проверка `isdigit`, уведомление в `ADMIN_CHAT_ID` (Username, Telegram ID, Broker ID), `set_step(main)`, `get_main_menu_keyboard`
- Helper `_format_user_info`

### Added — Stage 3: Handlers — /start и главное меню

- **handlers/start.py**: `cmd_start` — ТЗ text, `set_step(main)`, `get_main_menu_keyboard`
- «Получить доступ»: `set_step(choose_account_status)`, `get_account_status_keyboard`
- «Связаться с поддержкой»: `set_step(awaiting_support_message)`

### Added — Stage 2: Keyboards

- **keyboards/main_menu.py**: 4 new keyboards — `get_main_menu_keyboard`, `get_account_status_keyboard`, `get_new_registration_keyboard`, `get_existing_account_keyboard`
- Removed: `get_registration_choice_keyboard`, `get_registered_keyboard`, `get_send_id_keyboard`
- **keyboards/__init__.py**: Updated exports

### Added — MVP Funnel Stage 1: Config and state_manager

- **config.py**: `ADMIN_CHAT_ID` alias for `ADMIN_GROUP_CHAT_ID` (spec compliance)
- state_manager.py: unchanged (already supports required steps)

### Added — Stage 5: Router integration

- **handlers/__init__.py**: Exports `registration_router`, `admin_router`, `start_router`
- **app.py**: All routers (`start_router`, `registration_router`, `admin_router`) connected to `dp`
- MVP pipeline complete

### Added — Stage 4: Admin button handlers (approve/reject)

- **handlers/admin.py**: `admin_router` — callback `approve:{telegram_id}` (user gets success + SIGNAL_GROUP_LINK, admin message edited "Approved by @admin", clear_user); callback `reject:{telegram_id}` (user gets "ID не найден. Проверьте регистрацию.", admin group reply "Rejected by @admin", clear_user)
- **handlers/__init__.py**: Exports `admin_router`
- **app.py**: Includes `admin_router`

### Added — Stage 3: Registration handler (branches 1 and 2)

- **handlers/registration.py**: `registration_router` — branch "Зарегистрироваться" (affiliate link, instruction, "Я зарегистрировался" → set_step awaiting_id); branch "Я уже зарегистрирован" (support instruction, "Отправить ID" → set_step awaiting_id); ID input handler (set_broker_id, send to admin group with Approve/Reject, set_step id_submitted)
- **handlers/__init__.py**: Exports `registration_router`
- **app.py**: Includes `registration_router`

### Added — Stage 2: /start handler and offer flow

- **handlers/start.py**: `cmd_start` — sets step "main", greeting "Бот InTradeBar. Получите доступ к сигналам.", main menu with "Получить доступ" button
- **handlers/start.py**: `handle_get_access` — offer text, `get_registration_choice_keyboard()` with "Зарегистрироваться" | "Я уже зарегистрирован"
- **handlers/__init__.py**: Exports `start_router`

### Added — Stage 1: Config and keyboards

- **config.py**: `ADMIN_GROUP_CHAT_ID` (int), `SIGNAL_GROUP_LINK` (str), `AFFILIATE_LINK` (str)
- **keyboards/main_menu.py**: Main menu with "Получить доступ" button; `get_registration_choice_keyboard()`, `get_registered_keyboard()`, `get_send_id_keyboard()`
- **keyboards/inline_admin.py**: `get_approve_reject_keyboard(telegram_id: int)` for admin approve/reject actions
- **keyboards/__init__.py**: Exports for all keyboard factories
