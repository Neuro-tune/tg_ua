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
from bot.handlers import setup_routers

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
    
    # Notification to admin about startup
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="🟢 Bot successfully started and ready to work!"
        )
    except Exception as e:
        logger.warning(f"Failed to send notification to admin: {e}")


async def on_shutdown(bot: Bot) -> None:
    """Actions on bot shutdown"""
    logger.info("🔴 Bot stopped")
    
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="🔴 Bot stopped"
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
    
    # Register routers
    dp.include_router(setup_routers())
    
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