# Changelog

## [Unreleased]

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
