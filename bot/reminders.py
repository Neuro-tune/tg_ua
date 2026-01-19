import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from bot.services.google_sheets import GoogleSheetsService
from bot.config import config

logger = logging.getLogger(__name__)

class ReminderSystem:
    def __init__(self, bot: Bot, sheets_service: GoogleSheetsService):
        self.bot = bot
        self.sheets = sheets_service
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("🔔 Reminder system started")
        while self.is_running:
            try:
                await self.check_bookings()
            except Exception as e:
                logger.error(f"❌ Error in reminder loop: {e}")
            
            # Проверяем раз в 5 минут (300 сек), чтобы не спамить запросами
            await asyncio.sleep(300) 

    async def check_bookings(self):
        bookings = self.sheets.get_all_bookings()
        now = datetime.now()
        
        # Словарь месяцев для парсинга английских дат (если в таблице они на английском)
        # Если в таблице уже украинские даты, нужно будет адаптировать парсер
        # Пока предполагаем, что в таблице сохраняется формат из script.js (который мы перевели на укр)
        # Формат: "Пт, 16 січня 2026, 15:00"
        
        months_ua = {
            'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4, 'травня': 5, 'червня': 6,
            'липня': 7, 'серпня': 8, 'вересня': 9, 'жовтня': 10, 'листопада': 11, 'грудня': 12
        }

        for booking in bookings:
            # Формат в таблице: "Пт, 16 січня 2026, 15:00"
            date_str = booking.get('Visit Date/Time')
            user_id = booking.get('User ID')
            service = booking.get('Service')
            
            if not date_str or not user_id or user_id == 'ADMIN':
                continue

            try:
                # Парсим дату
                # 1. Убираем день недели "Пт, " -> "16 січня 2026, 15:00"
                # Но может быть и без дня недели, если старые записи.
                # Попробуем универсально.
                
                clean_str = date_str
                if ',' in date_str:
                    parts_comma = date_str.split(', ')
                    if len(parts_comma) > 2: # "Пт, 16 січня 2026, 15:00" -> ["Пт", "16 січня 2026", "15:00"]
                         # Это если формат "Day, Date, Time"
                         # В script.js мы делали: `${weekdays[date.getDay()]}, ${day} ${months[date.getMonth()]} ${date.getFullYear()}, ${timeValue}`
                         # То есть: "Пт, 16 січня 2026, 15:00"
                         # split(', ') даст: ["Пт", "16 січня 2026", "15:00"]
                         date_part = parts_comma[1] # "16 січня 2026"
                         time_part = parts_comma[2] # "15:00"
                    elif len(parts_comma) == 2:
                        # Может быть "Date, Time"
                        date_part = parts_comma[0]
                        time_part = parts_comma[1]
                    else:
                        continue
                else:
                    continue

                # date_part: "16 січня 2026"
                d_parts = date_part.split() # ["16", "січня", "2026"]
                
                day = int(d_parts[0])
                month = months_ua.get(d_parts[1].lower())
                year = int(d_parts[2])
                
                hour = int(time_part.split(':')[0])
                minute = int(time_part.split(':')[1])
                
                booking_dt = datetime(year, month, day, hour, minute)
                
                # --- ЛОГИКА НАПОМИНАНИЯ ---
                time_diff = booking_dt - now
                
                # Напоминание за 24 часа
                if timedelta(hours=23, minutes=55) < time_diff < timedelta(hours=24, minutes=5):
                    await self.send_reminder(user_id, service, date_str, "завтра")
                
                # Напоминание за 2 часа
                if timedelta(hours=1, minutes=55) < time_diff < timedelta(hours=2, minutes=5):
                    await self.send_reminder(user_id, service, date_str, "через 2 години")
                    
            except Exception as e:
                # logger.error(f"Date parse error for {date_str}: {e}")
                continue

    async def send_reminder(self, user_id, service, time_str, when_text):
        try:
            text = (
                f"🔔 <b>Нагадування про запис!</b>\n\n"
                f"Ви записані на <b>{service}</b> вже {when_text}.\n"
                f"🕒 Час: {time_str}\n\n"
                f"Чекаємо на вас!"
            )
            await self.bot.send_message(chat_id=user_id, text=text)
            logger.info(f"✅ Reminder sent to {user_id}")
        except Exception as e:
            logger.warning(f"Failed to send reminder to {user_id}: {e}")