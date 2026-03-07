"""Конфигурация CRM (Baserow). Переменные из env, fallback на пустые строки."""

import os

BASEROW_URL = os.environ.get("BASEROW_URL", "").rstrip("/")
BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN", "")
BASEROW_TABLE_ID = os.environ.get("BASEROW_TABLE_ID", "")
