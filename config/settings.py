import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHERSTACK_API_KEY = os.getenv("WEATHER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

CACHE_TTL = 300  # 5 минут

LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
ADMIN_IDS = {1343007129}