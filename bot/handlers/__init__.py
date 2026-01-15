"""
Handlers initialization
"""
from aiogram import Router
from .start import router as start_router
from .webapp import router as webapp_router


def setup_routers() -> Router:
    """Setup and merge routers"""
    main_router = Router()
    
    main_router.include_router(start_router)
    main_router.include_router(webapp_router)
    
    return main_router