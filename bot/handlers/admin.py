from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import config

router = Router(name="admin")

# ⚠️ УКАЖИ СВОЙ ID (число)
ADMIN_IDS = [543637202] 

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return 
    
    # Генерация ссылки на admin.html
    # Если webapp_url = https://site.com/index.html, превращаем в https://site.com/admin.html
    base_url = config.webapp_url.rsplit('/', 1)[0]
    admin_url = f"{base_url}/admin.html"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Відкрити Адмін Панель", web_app=WebAppInfo(url=admin_url))]
    ])
    
    await message.answer(
        "👋 Вітаю, адміністраторе! Керування записами:",
        reply_markup=kb
    )