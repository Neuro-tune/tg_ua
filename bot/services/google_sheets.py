"""
Service for working with Google Sheets
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for working with Google Sheets"""
    
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Заголовки таблицы (Английские, чтобы совпадать с ботом)
    HEADERS = [
        "ID", 
        "Booking Date", 
        "Name", 
        "Phone", 
        "Service", 
        "Visit Date/Time", 
        "User ID", 
        "Username"
    ]
    
    def __init__(self, credentials_file: str, sheet_name: str):
        self.credentials_file = credentials_file
        self.sheet_name = sheet_name
        self._client: Optional[gspread.Client] = None
        self._sheet: Optional[gspread.Spreadsheet] = None
        self._worksheet: Optional[gspread.Worksheet] = None
    
    def _connect(self) -> None:
        """Connect to Google Sheets"""
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, 
                self.SCOPES
            )
            self._client = gspread.authorize(credentials)
            self._sheet = self._client.open(self.sheet_name)
            self._worksheet = self._sheet.sheet1
            logger.info("✅ Successfully connected to Google Sheets")
        except Exception as e:
            logger.error(f"❌ Error connecting to Google Sheets: {e}")
            raise
    
    def _ensure_connection(self) -> None:
        """Check and restore connection"""
        if self._worksheet is None:
            self._connect()
    
    def _ensure_headers(self) -> None:
        """Check and create headers"""
        self._ensure_connection()
        
        try:
            first_row = self._worksheet.row_values(1)
            # Если первая строка пустая или заголовки не те
            if not first_row:
                self._worksheet.append_row(self.HEADERS)
                # Форматирование заголовков (синий фон, белый текст)
                self._worksheet.format('A1:H1', {
                    "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.9},
                    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "horizontalAlignment": "CENTER"
                })
                logger.info("✅ Headers created")
        except Exception as e:
            logger.error(f"❌ Error creating headers: {e}")
    
    async def add_booking(
        self, 
        name: str, 
        phone: str, 
        service: str, 
        date_time: str,
        user_id: int,
        username: str = ""
    ) -> dict:
        """
        Add booking to the sheet
        """
        self._ensure_headers()
        
        try:
            # Generate booking ID
            all_records = self._worksheet.get_all_values()
            booking_id = len(all_records)  # Booking number (row count including header)
            
            # Current date and time
            created_at = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Data for the row
            row_data = [
                booking_id,
                created_at,
                name,
                phone,
                service,
                date_time,
                user_id,
                username
            ]
            
            # Append row
            self._worksheet.append_row(row_data)
            
            logger.info(f"✅ Booking #{booking_id} added: {name} - {service}")
            
            return {
                "id": booking_id,
                "created_at": created_at,
                "name": name,
                "phone": phone,
                "service": service,
                "date_time": date_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error adding booking: {e}")
            raise
    
    def get_all_bookings(self) -> list:
        """Get all bookings"""
        self._ensure_connection()
        return self._worksheet.get_all_records()
    
    def get_bookings_count(self) -> int:
        """Get bookings count"""
        self._ensure_connection()
        return len(self._worksheet.get_all_values()) - 1 
    
    def get_bookings_by_user(self, user_id: int) -> List[Dict]:
        """
        Получение всех записей конкретного пользователя.
        """
        # Сначала получаем вообще все записи
        all_records = self.get_all_bookings()
        
        user_bookings = []
        # Превращаем ID пользователя в строку для надежного сравнения
        target_id = str(user_id)
        
        for record in all_records:
            # Получаем ID из строки (ключ должен совпадать с заголовком HEADERS)
            # Используем .get с защитой от пустых значений
            row_user_id = str(record.get("User ID") or record.get("user_id") or "")
            
            # Сравниваем строки
            if row_user_id == target_id:
                user_bookings.append(record)
                
        return user_bookings