"""Роутеры обработчиков."""

from aiogram import Router

from .crm_actions import router as crm_actions_router
from .crm_menu import router as crm_menu_router
from .crm_user_card import router as crm_user_card_router
from .leads_broadcast import router as leads_broadcast_router
from .registration import router as registration_router
from .start import router as start_router

crm_router = Router(name="crm")
crm_router.include_router(crm_menu_router)
crm_router.include_router(crm_user_card_router)
crm_router.include_router(crm_actions_router)
crm_router.include_router(leads_broadcast_router)

__all__ = ("crm_router", "registration_router", "start_router")
