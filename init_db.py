"""
Database initialisation script.
Run once to create the SQLite database file and all tables.

Usage:
    python init_db.py
"""
from database import engine, Base
from models import Article  # noqa: F401  – ensures the model is registered


def init():
    print("Resetting database tables …")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] Done. newsstand.db is reset and ready.")


if __name__ == "__main__":
    init()
