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
│   └── inline_admin.py # Approve/reject inline keyboard
├── handlers/
│   ├── start.py        # /start, main menu, «Получить доступ», «Связаться с поддержкой»
│   └── registration.py # Registration branches, ID input, support, fallback
├── services/
│   └── baserow.py      # Baserow CRM API (get_user, create_user, update_status, etc.)
└── state_manager.py
```

## Config

| Variable | Type | Description |
|----------|------|-------------|
| `ADMIN_GROUP_CHAT_ID` | int | Admin group chat ID (alias: `ADMIN_CHAT_ID`) |
| `SIGNAL_GROUP_LINK` | str | Link to signal group (for approved users) |
| `AFFILIATE_LINK` | str | Affiliate registration link |

**Admin notifications:** Messages sent to admin chat use format: emoji + header, user_info (Пользователь: @username or Без username), Broker ID (if applicable), action_text. Types: 🆕 Новая регистрация, 👤 Существующий аккаунт, 🔁 Запрос на переподключение, 💬 Сообщение от пользователя.

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
