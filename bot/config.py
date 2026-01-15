"""
Bot Configuration
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration class"""
    bot_token: str
    admin_id: int
    webapp_url: str
    google_sheet_name: str
    credentials_file: str = "credentials.json"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            admin_id=int(os.getenv("ADMIN_ID", 0)),
            webapp_url=os.getenv("WEBAPP_URL", ""),
            google_sheet_name=os.getenv("GOOGLE_SHEET_NAME", "Client Bookings"),
        )


config = Config.from_env()