"""
Main bot file
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from bot.config import config

# 🔥 ИМПОРТИРУЕМ НУЖНЫЕ МОДУЛИ
from bot.handlers import setup_routers, admin
from bot.reminders import ReminderSystem
from bot.services.google_sheets import GoogleSheetsService

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Actions on bot startup"""
    bot_info = await bot.get_me()
    logger.info(f"🚀 Bot @{bot_info.username} started!")
    
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="🟢 Бот успішно запущений і готовий до роботи!"
        )
    except Exception as e:
        logger.warning(f"Failed to send notification to admin: {e}")


async def on_shutdown(bot: Bot) -> None:
    """Actions on bot shutdown"""
    logger.info("🔴 Bot stopped")
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="🔴 Бот зупинений"
        )
    except Exception:
        pass


async def main() -> None:
    """Main function"""
    
    # Check configuration
    if not config.bot_token:
        logger.error("❌ BOT_TOKEN not specified in .env file!")
        return
    
    if not config.admin_id:
        logger.warning("⚠️ ADMIN_ID not specified, admin notifications disabled")
    
    if not config.webapp_url:
        logger.error("❌ WEBAPP_URL not specified in .env file!")
        return
    
    # Initialize bot
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # --- 🔥 НОВЫЙ БЛОК: ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ ---
    # 1. Подключаем таблицы
    sheets_service = GoogleSheetsService(config.credentials_file, config.google_sheet_name)
    
    # 2. Создаем систему напоминаний
    reminder_system = ReminderSystem(bot, sheets_service)
    
    # 3. Регистрируем роутеры (ВКЛЮЧАЯ АДМИНКУ)
    dp.include_router(setup_routers())
    dp.include_router(admin.router)  # <-- Важно! Без этого /admin не работает
    
    # 4. Запускаем напоминания в фоне
    asyncio.create_task(reminder_system.start())
    # ---------------------------------------------
    
    # Register events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start bot
    logger.info("🔄 Starting bot...")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")