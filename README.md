# Telegram Bot (MVP)

Aiogram 3.x bot with aiohttp webhook. **MVP funnel complete.** Content/buttons MVP: funnel texts and buttons use short, structured wording and emoji; button labels are centralized in `keyboards/main_menu.py` (BTN_* constants); all keyboards are InlineKeyboard; handlers use `callback_query`.

## Structure

```
telegram-bot/
├── app.py          # aiohttp app, webhook handler
├── config/         # Bot and CRM config
│   ├── __init__.py # BOT_TOKEN, webhook, ADMIN_CHAT_ID, SIGNAL_GROUP_LINK, AFFILIATE_LINK
│   └── crm.py      # Baserow env vars (BASEROW_URL, BASEROW_TOKEN, BASEROW_TABLE_ID)
├── keyboards/      # Inline keyboards
│   ├── main_menu.py    # BTN_* constants (8 buttons with emoji), main/account/new/existing keyboards
│   ├── inline_admin.py # Approve/reject inline keyboard
│   ├── crm_menu_kb.py  # CRM main menu
│   ├── crm_lists_kb.py # User list keyboards
│   └── crm_user_kb.py  # User card action keyboards
├── handlers/
│   ├── start.py        # /start, main menu, «Получить доступ», «Связаться с поддержкой»
│   ├── registration.py # Registration branches, ID input, support, fallback
│   ├── crm_menu.py     # /crm command, user lists
│   ├── crm_user_card.py# User card view
│   ├── crm_actions.py  # Access/reject/spam actions
│   └── leads_broadcast.py # /leads_send broadcast to leads
├── services/
│   ├── baserow.py      # Baserow API (get_user, create_user, get_recent_users, etc.)
│   └── crm_service.py  # CRM business logic (get_new_users, get_user_card, set_access_granted, etc.)
├── utils/
│   ├── admin_access.py  # has_crm_access — membership check in admin chat
│   └── format_helpers.py# format_datetime() — datetime formatting helper
└── state_manager.py
```

## Config

| Variable | Type | Description |
|----------|------|-------------|
| `ADMIN_CHAT_ID` | int | Admin chat ID (from env; used for notifications and CRM access) |
| `SIGNAL_GROUP_LINK` | str | Link to signal group (for approved users) |
| `AFFILIATE_LINK` | str | Affiliate registration link |

**Admin notifications:** Messages sent to admin chat use format: emoji + header, user_info (Пользователь: @username or Без username), Broker ID (if applicable), action_text. Types: 🆕 Новая регистрация, 👤 Существующий аккаунт, 🔁 Запрос на переподключение, 💬 Сообщение от пользователя.

## CRM

Admin panel for managing users. Access: only members of the chat with `ADMIN_CHAT_ID` (creator, administrator, member).

| Command | Description |
|---------|-------------|
| `/crm` | Open CRM menu (7 sections with counters) |
| `/leads_send` | Broadcast message to leads (target statuses: Новый пользователь, Начал регистрацию, Ожидаем Broker ID) |

**Broadcast flow:** Input text → mandatory confirmation → send or cancel. Report with sent/failed counts after completion.

**Sections (7):**

| Button | Description |
|--------|-------------|
| Готовы к подключению | Status: Broker ID получен |
| Ожидаем депозит | Status: Ожидаем депозит |
| Ожидаем Broker ID | Status: waiting |
| Новые лиды 24ч | Users created in last 24 hours |
| Поддержка | Support requests |
| Клиенты | Client users |
| Лиды | Leads (filtered by exclude statuses) |

**Lists:** Each section shows count in menu. All lists sorted by `created_at DESC`. List items display global position number and `created_at`.

**Pagination:** 10 users per page. Navigation: «⬅ Назад» (to menu), «Стр N/M», «➡ Далее». Page state restored when returning from user card.

**Actions:** View user card, grant access, reject, mark as spam, request deposit (💰 Запросить депозит — sets status to `Ожидаем депозит`, notifies user).

## Baserow CRM

Optional integration. If env vars are not set, CRM calls are no-op.

| Variable | Description |
|----------|-------------|
| `BASEROW_URL` | Baserow instance URL (e.g. `https://baserow.example.com`) |
| `BASEROW_TOKEN` | API token |
| `BASEROW_TABLE_ID` | Table ID for users |

**Table fields:** `telegram_id`, `telegram_username`, `first_name`, `status`, `last_event`, `created_at`, `broker_id`

**Funnel events (last_event):** `start`, `registration_started`, `broker_id_submitted`, `support_message`

**Integration points:** `cmd_start` (create/get user), `handle_get_access` (update status), `_handle_id_submission` (broker_id, status), `handle_support_message_input` (status)

## Run

```bash
python app.py
```
