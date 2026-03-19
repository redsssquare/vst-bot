# Changelog

## [Unreleased]

### Bugfix: Media messages dropped in crm_write state (2026-03-19)

**Проблема:** Фото, документы и другие медиа, отправленные менеджером CRM в состоянии `crm_write`, не пересылались пользователю — они молча игнорировались.

**Причина:**
- Фильтр `F.text` на `@router.message` отклонял все нетекстовые сообщения до входа в обработчик
- `bot.send_message()` поддерживает только текст, что делало пересылку медиа невозможной даже при исправлении фильтра

**Исправление:**
- Удалён фильтр `F.text` из `@router.message` — обработчик теперь срабатывает для всех типов сообщений в состоянии `crm_write`
- `await message.bot.send_message(target_id, text)` заменено на `await message.copy_to(target_id)` — работает универсально для любого типа контента

**Изменённые файлы:**
- `handlers/crm_actions.py` (строки 76–97)

---

### Broadcast /leads_send (2026-03-18)

**Новые файлы:**
- `handlers/leads_broadcast.py` — команда `/leads_send`, flow рассылки (ввод текста → подтверждение → отправка/отмена), отчёт

**Изменённые файлы:**
- `services/baserow.py` — `_BROADCAST_LEAD_STATUSES` (Новый пользователь, Начал регистрацию, Ожидаем Broker ID), `get_leads_telegram_ids_for_broadcast()`
- `services/crm_service.py` — `get_leads_broadcast_telegram_ids()`
- `state_manager.py` — `set_broadcast_text`, `get_broadcast_text`, `clear_broadcast_text`
- `handlers/__init__.py` — добавлен `leads_broadcast_router` в `crm_router`

**Функции:**
- `/leads_send` — рассылка сообщения лидам с целевыми статусами
- Flow: ввод текста → обязательное подтверждение → отправка или отмена
- Отчёт: количество отправленных и неудачных сообщений

---

### CRM воронка — расширение (2026-03-18)

**Новые файлы:**
- `utils/format_helpers.py` — `format_datetime()` для форматирования дат
- `utils/__init__.py` — экспорт `format_datetime`

**Изменённые файлы:**
- `config/__init__.py` — добавлена константа `STATUS_WAITING_DEPOSIT = "Ожидаем депозит"`
- `services/baserow.py` — добавлены `_LEADS_EXCLUDE_STATUSES`, `get_leads_users()`, `get_leads_count()`
- `services/crm_service.py` — добавлены `get_waiting_deposit`, `get_waiting_deposit_count`, `get_clients`, `get_clients_count`, `get_leads`, `get_leads_count`, `set_waiting_deposit`; `get_menu_counts()` возвращает 7 ключей (без `all`)
- `keyboards/crm_menu_kb.py` — перестроено меню: 7 кнопок (ready, deposit, waiting, new_leads, support, clients, leads); удалена кнопка «Все пользователи»
- `keyboards/crm_lists_kb.py` — `get_user_list_keyboard` принимает `page_offset`; кнопки показывают глобальный номер пользователя
- `keyboards/crm_user_kb.py` — добавлена кнопка «💰 Запросить депозит»
- `handlers/crm_menu.py` — удалён `handle_crm_all`; добавлены `handle_crm_deposit`, `handle_crm_clients`, `handle_crm_leads`; `_format_user_list` принимает `page_offset` и отображает `created_at`; обновлён regexp пагинации и ветки `back_to_list`
- `handlers/crm_user_card.py` — в `handle_crm_next_lead` добавлены ветки для `deposit`, `clients`, `leads`; используется `format_datetime`
- `handlers/crm_actions.py` — добавлены `handle_crm_deposit_request`, `handle_crm_deposit_confirm`, константа `DEPOSIT_MESSAGES`; используется `format_datetime`
- `handlers/registration.py` — добавлена `FALLBACK_TEXT`; `handle_text_fallback` не сбрасывает шаг пользователя

**Новые разделы CRM:**
- «💰 Ожидаем депозит» — пользователи со статусом `STATUS_WAITING_DEPOSIT`
- «👥 Клиенты» — пользователи-клиенты
- «🔥 Лиды» — лиды, отфильтрованные по `_LEADS_EXCLUDE_STATUSES`

**Новое действие:**
- «💰 Запросить депозит» в карточке пользователя — устанавливает статус `STATUS_WAITING_DEPOSIT`, отправляет сообщение пользователю

---

### CRM Menu and Lists Update (2025-03-07)

**Изменённые файлы:**
- `services/crm_service.py` — логика секций, счётчики, «Готовы к подключению»
- `keyboards/crm_menu_kb.py` — 5 секций с counters
- `keyboards/crm_lists_kb.py` — пагинация ⬅ Пред | Стр N/M | ➡ Далее | ⬅ В меню
- `keyboards/crm_user_kb.py` — кнопка «➡ Следующий лид»
- `handlers/crm_menu.py` — обработка секций, пагинация
- `handlers/crm_user_card.py` — «Следующий лид», «Список лидов завершён»
- `handlers/crm_actions.py` — интеграция с новым state
- `state_manager.py` — crm_list_users, crm_list_user_index, crm_list_total

**Функции:**
- CRM меню: 5 секций (Готовы к подключению, Ожидаем Broker ID, Новые пользователи 24ч, Поддержка, Все пользователи) с counters
- Секция «Готовы к подключению» — status = Broker ID получен
- Пагинация: ⬅ Пред, Стр N/M, ➡ Далее, ⬅ В меню
- Формат списка Поддержка: Имя, Username, Последнее сообщение («—» если нет поля)
- Кнопка «➡ Следующий лид» в карточке — переход к следующему или «Список лидов завершён»
- State: crm_list_users, crm_list_user_index, crm_list_total

---

### CRM MVP UX + Lead Queue + Pagination (2025-03-07)

**Изменённые файлы:**
- `services/baserow.py` — get_users_by_status(limit, offset), get_users_created_after_24h, get_new_leads_count, get_recent_users(offset), _parse_created_at
- `services/crm_service.py` — get_new_leads_24h, get_new_leads_count, get_menu_counts(new_leads), get_recent_users(offset)
- `keyboards/crm_menu_kb.py` — пункт «🆕 Новые лиды (N)» первым, порядок new_leads, waiting, new, support, all
- `keyboards/crm_lists_kb.py` — пагинация: list_type, page, total_pages, навигация «⬅ Назад | Стр N/M | ➡ Далее»
- `handlers/crm_menu.py` — crm_new_leads, handle_crm_list_page (crm_*_page_{n}), crm_noop, пагинация 10/страница
- `state_manager.py` — set_crm_list_page, get_crm_list_page

**Функции:**
- Раздел «Новые лиды (24ч)» — пользователи за последние 24 часа
- Пагинация 10 пользователей на страницу, edit_message_text при переключении
- Сортировка ORDER BY created_at DESC во всех списках
- crm_back_to_list восстанавливает страницу из state

**send_message(user_id):** не используется в действиях Доступ выдан / Отклонен / Спам

---

### CRM UI and Logic (2025-03-07)

**Изменённые файлы:**
- `handlers/crm_actions.py` — удалены send_message(user) для действий Доступ выдан/Отклонен/Спам; debug-логи status updated
- `handlers/crm_menu.py` — counters в меню, статус в списках, crm_back_to_menu, crm_back_to_list, set_crm_list_source, debug-логи
- `handlers/crm_user_card.py` — debug-логи user card opened
- `keyboards/crm_menu_kb.py` — параметр counts, формат кнопок с (N)
- `keyboards/crm_lists_kb.py` — кнопка «⬅ Назад»
- `keyboards/crm_user_kb.py` — кнопка «⬅ Назад» в карточке
- `services/baserow.py` — get_total_rows_count()
- `services/crm_service.py` — get_waiting_count, get_new_count, get_support_count, get_all_users_count, get_menu_counts
- `state_manager.py` — set_crm_list_source, get_crm_list_source

**Исправления:**
- Действия «Доступ выдан», «Отклонен», «Спам» больше не отправляют сообщения пользователю (только update_status, log_event, обновление карточки)
- Добавлены counters в CRM меню
- Добавлен статус в списках пользователей
- Добавлена кнопка «Назад» в списках и карточке
- Добавлено debug-логирование CRM

**Сценарий menu → list → user → back → back:** реализован и проверен (импорты OK)

**send_message(user_id):** не используется в действиях Доступ выдан / Отклонен / Спам. «Написать» — отдельный flow по запросу менеджера.

---

### CRM module (2025-03-07)

- **config/__init__.py**: `ADMIN_CHAT_ID` from env (fallback `-5253061936`).
- **utils/admin_access.py**: `has_crm_access(bot, user_id)` — checks membership in admin chat (creator/administrator/member).
- **services/baserow.py**: `get_recent_users`, `_row_to_user_dict` extended with `id`, `created_at`.
- **services/crm_service.py**: `get_new_users`, `get_waiting_broker_id`, `get_support_requests`, `get_recent_users`, `get_user_card`, `set_access_granted`, `set_rejected`, `set_spam`.
- **keyboards/crm_menu_kb.py**: `get_crm_menu_keyboard()` — main CRM menu.
- **keyboards/crm_lists_kb.py**: `get_user_list_keyboard(users)` — user list with cards.
- **keyboards/crm_user_kb.py**: user card actions (access/reject/spam).
- **state_manager.py**: `set_crm_write_target`, `get_crm_write_target`, `clear_crm_write_target`.
- **handlers/crm_menu.py**: `/crm` command, lists (waiting, new, support, all).
- **handlers/crm_user_card.py**: user card view, navigation.
- **handlers/crm_actions.py**: access granted, rejected, spam actions.
- **app.py**: `crm_router` registered.
- **Structural:** `utils/` package (`admin_access.py`), `handlers/crm_menu.py`, `handlers/crm_user_card.py`, `handlers/crm_actions.py`, `keyboards/crm_menu_kb.py`, `keyboards/crm_lists_kb.py`, `keyboards/crm_user_kb.py`, `services/crm_service.py`.

### Baserow CRM integration

- **config/crm.py**: `BASEROW_URL`, `BASEROW_TOKEN`, `BASEROW_TABLE_ID` from env (fallback empty).
- **services/baserow.py**: `get_user_by_telegram_id`, `create_user`, `update_status`, `update_broker_id`, `log_event`. No-op when CRM not configured.
- **handlers/start.py**: `cmd_start` — create user if new; `handle_get_access` — update status to "Начал регистрацию", event `registration_started`.
- **handlers/registration.py**: `_handle_id_submission` — update `broker_id`, status "Broker ID получен", event `broker_id_submitted`; `handle_support_message_input` — status "Сообщение в поддержку", event `support_message`.
- **Structural:** `config/` package (crm.py), `services/` package (baserow.py); `config.py` removed.

### Stage 1: Admin chat messages refactor

- **handlers/registration.py**: `_format_user_info` — returns "Пользователь: @username" or "Пользователь: Без username" (no Telegram ID).
- `_handle_id_submission` — new format: emoji + header, user_info, Broker ID, action_text.
- 4 admin message types: 🆕 Новая регистрация, 👤 Существующий аккаунт, 🔁 Запрос на переподключение, 💬 Сообщение от пользователя.
- `handle_reconnect_request` — sends admin notification when user clicks "Помогите переподключить".

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
