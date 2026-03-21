"""
APScheduler configuration.
Runs the news collection job daily at 08:00 KST.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import FETCH_HOUR, FETCH_MINUTE, TIMEZONE
from collector import run_collection

logger = logging.getLogger(__name__)


def start_scheduler() -> BackgroundScheduler:
    """Create, configure, and start the background scheduler."""
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_collection,
        trigger=CronTrigger(
            hour=FETCH_HOUR,
            minute=FETCH_MINUTE,
            timezone=TIMEZONE,
        ),
        id="daily_news_collection",
        name="Daily News Collection (08:00 KST)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started: daily collection at %02d:%02d %s",
        FETCH_HOUR, FETCH_MINUTE, TIMEZONE,
    )
    return scheduler
