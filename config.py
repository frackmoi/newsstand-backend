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
# DATABASE_URL must be set as an environment variable (e.g. Render dashboard).
# Format: postgresql://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please configure it in Render dashboard (or .env for local dev)."
    )
# SQLAlchemy requires 'postgresql+psycopg2://' not the 'postgres://' alias
# that Supabase/Heroku sometimes returns.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Scheduler ──────────────────────────────────────────
FETCH_HOUR = 8   # KST 08:00
FETCH_MINUTE = 0
TIMEZONE = "Asia/Seoul"
