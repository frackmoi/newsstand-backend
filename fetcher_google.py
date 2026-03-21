"""
Google News RSS fetcher for the Global (글로벌) category.

Uses Google News RSS feed to fetch top international news.
Filters out entertainment content with a keyword blocklist.
"""
import re
import html
import logging
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser

logger = logging.getLogger(__name__)

# Google News RSS — Top Headlines (Korean edition for relevance)
GOOGLE_RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
# Google News RSS Topics for Regions
GOOGLE_RSS_REGIONS = {
    "글로벌": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
    "미주": "https://news.google.com/rss/topics/CAAqI0gKIhtDQVFTWlI0S0Vnd2liV1IxWTJOcmVpZ0FQAigB?hl=ko&gl=KR&ceid=KR:ko",
    "유럽": "https://news.google.com/rss/topics/CAAqI0gKIhtDQVFTWlI0S0Vnd2liV1IxWTJOcmVpZ0FQAigC?hl=ko&gl=KR&ceid=KR:ko",
    "아시아": "https://news.google.com/rss/topics/CAAqI0gKIhtDQVFTWlI0S0Vnd2liV1IxWTJOcmVpZ0FQAigD?hl=ko&gl=KR&ceid=KR:ko",
}

# ── Entertainment blocklist (same as Naver) ──────────────────────
BLOCK_KEYWORDS = [
    "연예", "방송", "아이돌", "드라마", "예능", "가수", "배우",
    "걸그룹", "보이그룹", "팬미팅", "콘서트", "엔터테인먼트",
]
BLOCK_PATTERN = re.compile("|".join(BLOCK_KEYWORDS))


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    clean = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(clean).strip()


def _is_blocked(title: str, description: str) -> bool:
    """Reject if title or description matches the entertainment blocklist."""
    combined = f"{title} {description}"
    return bool(BLOCK_PATTERN.search(combined))


def _parse_pub_date(entry) -> datetime | None:
    """Try to parse the publication date from a feedparser entry."""
    raw = entry.get("published", "")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        # Ensure it's offset-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        logger.warning("Failed to parse Google RSS date '%s': %s", raw, e)
        return None


async def fetch_google_global(max_items: int = 50) -> list[dict]:
    """
    Parse multiple Google News Region RSS feeds and return aggregated rows.
    """
    results: list[dict] = []
    # KST is UTC+9
    now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    today = now_kst.date()

    for region_name, rss_url in GOOGLE_RSS_REGIONS.items():
        logger.info(f"Fetching Google RSS for region: {region_name}")
        feed = feedparser.parse(rss_url)

        if feed.bozo and not feed.entries:
            logger.error(f"Google RSS parse error for {region_name}: {feed.bozo_exception}")
            continue

        region_count = 0
        for entry in feed.entries:
            if region_count >= 20: # Limit per sub-region to keep balance
                break

            title = _strip_html(entry.get("title", ""))
            description = _strip_html(entry.get("summary", ""))

            if _is_blocked(title, description):
                continue

            pub_dt = _parse_pub_date(entry)
            
            # STRICT DATE FILTER: Only include articles published TODAY (KST)
            if pub_dt:
                pub_kst = pub_dt.astimezone(timezone(timedelta(hours=9)))
                if pub_kst.date() != today:
                    continue
            else:
                continue

            link = entry.get("link", "")
            results.append({
                "category": "글로벌",
                "sub_category": region_name if region_name != "글로벌" else None,
                "title": title,
                "link": link,
                "description": description,
                "pub_date": pub_dt,
                "fetch_date": today,
                "source": "google",
            })
            region_count += 1

    logger.info("Google RSS | Aggregated %d global items across regions", len(results))
    return results
