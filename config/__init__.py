"""Конфигурация бота. Единственное место для глобальных настроек."""

import os

BOT_TOKEN = "8794604330:AAFK-69PN5ACz1OLNiy4wSh59wZj2dt0JAE"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://bot.yurinartur.com/webhook"

def _parse_admin_chat_id() -> int:
    raw = os.environ.get("ADMIN_CHAT_ID", "-5253061936")
    if not raw or not raw.strip():
        return -5253061936
    try:
        return int(raw)
    except ValueError:
        return -5253061936


ADMIN_CHAT_ID: int = _parse_admin_chat_id()
SIGNAL_GROUP_LINK: str = "https://t.me/trade_riski"  # TODO: set link to signal group for approve
AFFILIATE_LINK: str = os.environ.get("AFFILIATE_LINK", "https://intrade30.bar/854761")

# CRM статусы (строго использовать эти строки)
STATUS_NEW = "Новый пользователь"
STATUS_REGISTRATION_STARTED = "Начал регистрацию"
STATUS_WAITING_BROKER_ID = "Ожидаем Broker ID"
STATUS_BROKER_ID_RECEIVED = "Broker ID получен"
STATUS_ACCESS_GRANTED = "Доступ выдан"
STATUS_SUPPORT_MESSAGE = "Сообщение в поддержку"
STATUS_REJECTED = "Отклонен"
STATUS_SPAM = "Спам"
