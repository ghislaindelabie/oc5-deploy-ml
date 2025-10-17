# app/config.py
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env if present

APP_ENV = os.getenv("APP_ENV", "dev")
DB_URL = os.getenv("DB_URL", "sqlite:///./local.db")
API_KEY = os.getenv("API_KEY", "")