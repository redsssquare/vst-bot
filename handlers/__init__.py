"""Роутеры обработчиков."""

from .registration import router as registration_router
from .start import router as start_router

__all__ = ("registration_router", "start_router")
