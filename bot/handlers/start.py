"""
Reply Keyboard Handler for /start command
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from bot.config import config
# Import the Google Sheets Service
from bot.services.google_sheets import GoogleSheetsService

router = Router(name="start")

# Initialize the Google Sheets Service
# This allows us to check bookings in the handlers below
sheets_service = GoogleSheetsService(config.credentials_file, config.google_sheet_name)


def get_webapp_keyboard() -> ReplyKeyboardMarkup:
    """
    Reply Keyboard with Web App button
    THIS IS THE ONLY WAY sendData() works!
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📝 Записатися",
                    web_app=WebAppInfo(url=config.webapp_url)
                )
            ],
            [
                KeyboardButton(text="📞 Контакти"),
                KeyboardButton(text="ℹ️ Про нас")
            ],
            [
                KeyboardButton(text="📋 Мої записи")
            ]
        ],
        resize_keyboard=True,  # Reduce button size
        is_persistent=True     # Keyboard always visible
    )
    return keyboard


def get_inline_keyboard() -> InlineKeyboardMarkup:
    """Additional Inline buttons (without Web App)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Наш сайт",
                    url="https://example.com"
                ),
                InlineKeyboardButton(
                    text="📱 Instagram",
                    url="https://instagram.com/example"
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handler for /start command"""
    
    welcome_text = f"""
👋 <b>Вітаємо, {message.from_user.first_name}!</b>

🏥 Ми раді вітати вас у нашому сервісі онлайн-запису.

✨ <b>Що ми пропонуємо:</b>
• Зручний запис у кілька кліків
• Вибір зручного часу
• Нагадування про візит
• Історія ваших записів

👇 <b>Натисніть кнопку нижче, щоб записатися:</b>
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_webapp_keyboard(),
        parse_mode="HTML"
    )


# Text Reply Keyboard Button Handlers
@router.message(F.text == "📞 Контакти")
async def handle_contact(message: Message) -> None:
    """Handler for 'Contact Us' button"""
    contact_text = """
📞 <b>Наші контакти:</b>

📱 Телефон: +380 (99) 123-45-67
📧 Email: info@example.com
🕐 Час роботи: Пн-Пт 9:00 - 20:00

📍 Адреса: Київ, вул. Прикладна, 1
"""
    await message.answer(contact_text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Про нас")
async def handle_about(message: Message) -> None:
    """Handler for 'About Us' button"""
    about_text = """
ℹ️ <b>Про нашу компанію</b>

Ми працюємо з 2020 року та надаємо
якісні послуги нашим клієнтам.

🏆 Понад 1000 задоволених клієнтів
⭐ Рейтинг 4.9 на картах
👨‍⚕️ Досвідчені спеціалісти
"""
    await message.answer(about_text, parse_mode="HTML")


@router.message(F.text == "📋 Мої записи")
async def handle_my_bookings(message: Message) -> None:
    """Handler for 'My Bookings' button - REAL DATA CHECK"""
    
    # 1. Get the Telegram User ID
    user_id = message.from_user.id
    
    try:
        # 2. Request bookings from Google Sheets
        bookings = sheets_service.get_bookings_by_user(user_id)
        
        # 3. If no bookings found
        if not bookings:
            await message.answer(
                "📂 <b>У вас поки немає активних записів.</b>",
                parse_mode="HTML"
            )
            return

        # 4. If bookings exist, format the message
        response_text = "📋 <b>Ваші активні записи:</b>\n"
        
        for booking in bookings:
            # Get data from dictionary (keys match Google Sheet headers)
            service = booking.get("Service", "Service")
            date_time = booking.get("Visit Date/Time", "Time not specified")
            
            response_text += f"\n🔹 <b>{service}</b>"
            response_text += f"\n🕒 {date_time}"
            response_text += "\n───────────────"

        await message.answer(response_text, parse_mode="HTML")

    except Exception as e:
        # Error handling (e.g., connection issue)
        import traceback
        print("❌ КРИТИЧЕСКАЯ ОШИБКА В MY BOOKINGS:")
        print(e)
        print(traceback.format_exc())
        await message.answer(
            "⚠️ <b>Помилка отримання даних.</b>\nСпробуйте пізніше.",
            parse_mode="HTML"
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Show main menu"""
    await message.answer(
        "📱 <b>Головне меню</b>\n\nОберіть дію:",
        reply_markup=get_webapp_keyboard(),
        parse_mode="HTML"
    )