# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Admin Password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Database Path
DATABASE_PATH = os.getenv("DATABASE_PATH", "defects.db")