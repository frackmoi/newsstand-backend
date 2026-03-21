"""
Unified news collector.

Orchestrates Naver and Google fetchers, deduplicates by link,
and saves new articles into the SQLite database.
"""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Article
from fetcher_naver import fetch_all_naver
from fetcher_google import fetch_google_global

logger = logging.getLogger(__name__)


def _save_articles(db: Session, rows: list[dict]) -> int:
    """
    Insert articles that don't already exist (deduplicate by link + fetch_date).
    Returns the count of newly inserted articles.
    """
    inserted = 0
    for row in rows:
        try:
            exists = (
                db.query(Article.id)
                .filter(
                    or_(
                        Article.link == row["link"],
                        Article.title == row["title"]
                    )
                )
                .first()
            )
            if exists:
                continue

            article = Article(**row)
            db.add(article)
            inserted += 1
        except Exception as e:
            logger.error(f"Error saving article {row.get('title', 'Unknown')}: {e}")
            db.rollback()
            continue

    db.commit()
    return inserted


async def _collect_async() -> dict:
    """Run both fetchers concurrently and return aggregated rows."""
    naver_rows, google_rows = await asyncio.gather(
        fetch_all_naver(),
        fetch_google_global(),
    )
    return {
        "naver": naver_rows,
        "google": google_rows,
    }


def run_collection() -> dict:
    """
    Main entry point for the scheduled job (synchronous wrapper).
    Fetches from all sources, saves to DB, and returns a summary.
    """
    logger.info("=== News collection started ===")

    result = asyncio.run(_collect_async())
    all_rows = result["naver"] + result["google"]

    db = SessionLocal()
    try:
        inserted = _save_articles(db, all_rows)
    finally:
        db.close()

    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date()
    summary = {
        "date": str(today_kst),
        "naver_fetched": len(result["naver"]),
        "google_fetched": len(result["google"]),
        "total_fetched": len(all_rows),
        "new_inserted": inserted,
    }
    logger.info("=== Collection complete: %s ===", summary)
    return summary


# ── CLI entry point for manual testing ───────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = run_collection()
    print("\n--- Collection Summary ---")
    for k, v in result.items():
        print(f"  {k}: {v}")
