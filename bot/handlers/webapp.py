"""
Handler for Web App data
"""
import json
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from bot.config import config
from bot.services.google_sheets import GoogleSheetsService

router = Router(name="webapp")
logger = logging.getLogger(__name__)

# Initialize Google Sheets service
sheets_service = GoogleSheetsService(
    credentials_file=config.credentials_file,
    sheet_name=config.google_sheet_name
)


def format_booking_message(booking: dict, user_info: str = "") -> str:
    """Format booking message"""
    return f"""
🎉 <b>New Booking #{booking['id']}</b>

👤 <b>Client:</b> {booking['name']}
📱 <b>Phone:</b> {booking['phone']}
💼 <b>Service:</b> {booking['service']}
📅 <b>Date/Time:</b> {booking['date_time']}
🕐 <b>Created:</b> {booking['created_at']}
{user_info}
"""


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, bot: Bot) -> None:
    """Handle data from Web App"""
    
    try:
        # Parse data from Web App
        data = json.loads(message.web_app_data.data)
        
        logger.info(f"📥 Received data from Web App: {data}")
        
        # Validate data
        required_fields = ['name', 'phone', 'service', 'datetime']
        for field in required_fields:
            if field not in data or not data[field]:
                await message.answer(
                    f"❌ Error: field '{field}' is required"
                )
                return
        
        # Save to Google Sheets
        booking = await sheets_service.add_booking(
            name=data['name'],
            phone=data['phone'],
            service=data['service'],
            date_time=data['datetime'],
            user_id=message.from_user.id,
            username=message.from_user.username or ""
        )
        
        # Confirmation to user
        user_message = f"""
✅ <b>Booking successfully created!</b>

📋 <b>Booking Details:</b>
├ 🆔 Number: #{booking['id']}
├ 👤 Name: {booking['name']}
├ 📱 Phone: {booking['phone']}
├ 💼 Service: {booking['service']}
└ 📅 Date/Time: {booking['date_time']}

⏰ We will remind you about your visit!
📞 If you need to cancel or reschedule, please contact us.

Thank you for choosing us! 💙
"""
        
        await message.answer(user_message, parse_mode="HTML")
        
        # Notification to admin
        user_info = f"👤 <b>Telegram:</b> @{message.from_user.username}" if message.from_user.username else f"👤 <b>User ID:</b> {message.from_user.id}"
        
        admin_message = format_booking_message(booking, user_info)
        admin_message += "\n━━━━━━━━━━━━━━━━━━━━━━"
        
        try:
            await bot.send_message(
                chat_id=config.admin_id,
                text=admin_message,
                parse_mode="HTML"
            )
            logger.info(f"✅ Notification sent to admin (ID: {config.admin_id})")
        except Exception as e:
            logger.error(f"❌ Error sending notification to admin: {e}")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing error: {e}")
        await message.answer("❌ Error processing data. Please try again.")
        
    except Exception as e:
        logger.error(f"❌ Error processing Web App data: {e}")
        await message.answer(
            "❌ An error occurred while creating the booking.\n"
            "Please try again later or contact us."
        )