"""
Application configuration.
Loads environment variables from .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Naver API ──────────────────────────────────────────
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ── Database ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'newsstand.db')}"

# ── Scheduler ──────────────────────────────────────────
FETCH_HOUR = 8   # KST 08:00
FETCH_MINUTE = 0
TIMEZONE = "Asia/Seoul"
