"""Конфигурация CRM (Baserow). Переменные из env, fallback на пустые строки."""

import os

BASEROW_URL = os.environ.get("BASEROW_URL", "").rstrip("/")
BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN", "")
BASEROW_TABLE_ID = os.environ.get("BASEROW_TABLE_ID", "")
# ID поля «Последнее сообщение в поддержку» (Long text). last_message = field_7459
BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID = os.environ.get("BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID", "field_7459")
