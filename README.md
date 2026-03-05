# Telegram Bot (MVP)

Aiogram 3.x bot with aiohttp webhook. **MVP funnel complete.** Content/buttons MVP: funnel texts and buttons use short, structured wording and emoji; button labels are centralized in `keyboards/main_menu.py` (BTN_* constants); all keyboards are InlineKeyboard; handlers use `callback_query`.

## Structure

```
telegram-bot/
├── app.py          # aiohttp app, webhook handler
├── config.py       # BOT_TOKEN, webhook, ADMIN_GROUP_CHAT_ID, SIGNAL_GROUP_LINK, AFFILIATE_LINK
├── keyboards/      # Inline keyboards
│   ├── main_menu.py    # BTN_* constants (8 buttons with emoji), main/account/new/existing keyboards
│   └── inline_admin.py # Approve/reject inline keyboard
├── handlers/
│   ├── start.py        # /start, main menu, «Получить доступ», «Связаться с поддержкой»
│   └── registration.py # Registration branches, ID input, support, fallback
└── state_manager.py
```

## Config

| Variable | Type | Description |
|----------|------|-------------|
| `ADMIN_GROUP_CHAT_ID` | int | Admin group chat ID |
| `SIGNAL_GROUP_LINK` | str | Link to signal group (for approved users) |
| `AFFILIATE_LINK` | str | Affiliate registration link |

## Run

```bash
python app.py
```
