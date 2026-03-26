"""
Naver News API fetcher.

Fetches news for 사회, 경영경제, 인사노무 categories.
Strictly excludes entertainment-related results via query keywords
and a focused post-filter.
"""
import re
import html
import logging
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx

from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

logger = logging.getLogger(__name__)

NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"

# ── Entertainment blocklist (post-filter) ────────────────────────
# Kept focused on clearly entertainment-only words to avoid false positives
BLOCK_KEYWORDS = [
    "연예", "아이돌", "걸그룹", "보이그룹",
    "팬미팅", "엔터테인먼트", "컴백무대", "뮤직비디오",
    "K-POP", "KPOP", "케이팝", "오디션",
    "화보", "데뷔", "콘서트", "드라마",
]
BLOCK_PATTERN = re.compile("|".join(BLOCK_KEYWORDS))

# ── Query definitions per category ───────────────────────────────
# Strategy: use specific topic keywords to get relevant news.
# Naver API negative keywords handle broad entertainment exclusion.
CATEGORY_QUERIES: dict[str, list[dict]] = {
    "사회": [
        {"query": "사회 이슈", "sub_category": None},
        {"query": "정치 뉴스", "sub_category": None},
        {"query": "정부 정책", "sub_category": None},
        {"query": "사건 사고", "sub_category": None},
    ],
    "경영경제": [
        {"query": "경제 전망", "sub_category": None},
        {"query": "경영 비즈니스", "sub_category": None},
        {"query": "금리 환율", "sub_category": None},
        {"query": "기업 동향", "sub_category": None},
    ],
    "인사노무": [
        {"query": "인사 채용", "sub_category": "핫이슈"},
        {"query": "노동 노무 이슈", "sub_category": "핫이슈"},
        {"query": "근로기준법 개정", "sub_category": "법령/근로기준법"},
        {"query": "대법원 판례", "sub_category": "법령개정/판례"},
    ],
    "글로벌": [
        {"query": "미국 뉴스", "sub_category": "미주"},
        {"query": "유럽 뉴스", "sub_category": "유럽"},
        {"query": "아시아 뉴스", "sub_category": "아시아"},
        {"query": "세계 정세", "sub_category": None},
    ],
}


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    clean = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(clean).strip()


def _is_blocked(title: str, description: str) -> bool:
    """Secondary filter: reject only if title/description has clearly entertainment content."""
    combined = f"{title} {description}"
    return bool(BLOCK_PATTERN.search(combined))


def _parse_pub_date(raw: str) -> datetime | None:
    """Parse RFC-822 date string from Naver API into a datetime."""
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        # Ensure it's offset-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        logger.warning("Failed to parse pubDate '%s': %s", raw, e)
        return None


async def fetch_naver_category(
    category: str,
    query: str,
    sub_category: str | None,
    display: int = 100,
) -> list[dict]:
    """
    Call Naver News Search API for a single query and return cleaned rows.
    """
    # Normalize category name just in case
    cat_map = {"경제": "경영경제", "경영": "경영경제", "사회": "사회", "인사": "인사노무", "노무": "인사노무"}
    norm_cat = cat_map.get(category, category)

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "date",  # most recent first
    }

    results: list[dict] = []
    # KST is UTC+9
    now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    today = now_kst.date()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(NAVER_SEARCH_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("Naver API error for query '%s': %s", query, exc)
        return results

    raw_items = data.get("items", [])
    filtered_out = 0
    blocked_out = 0

    for item in raw_items:
        title = _strip_html(item.get("title", ""))
        description = _strip_html(item.get("description", ""))

        # Post-filter: skip entertainment content
        if _is_blocked(title, description):
            blocked_out += 1
            continue

        pub_dt = _parse_pub_date(item.get("pubDate", ""))
        
        # STRICT DATE FILTER: Only include articles published TODAY (KST)
        if pub_dt:
            # Convert pub_dt to KST for comparison if it's offset-aware
            pub_kst = pub_dt.astimezone(timezone(timedelta(hours=9)))
            if pub_kst.date() != today:
                filtered_out += 1
                continue
        else:
            # If we can't parse the date, we skip it to be safe
            filtered_out += 1
            continue

        results.append({
            "category": norm_cat,
            "sub_category": sub_category,
            "title": title,
            "link": item.get("originallink") or item.get("link", ""),
            "description": description,
            "pub_date": pub_dt,
            "fetch_date": today,
            "source": "naver",
        })

    logger.info(
        "Naver | %s | %d results (Filtered: %d, Blocked: %d, Total Raw: %d) Query: %s",
        norm_cat, len(results), filtered_out, blocked_out, len(raw_items), query
    )
    return results


async def fetch_all_naver() -> list[dict]:
    """
    Run every Naver query across all categories and return aggregated rows.
    """
    all_rows: list[dict] = []
    for category, queries in CATEGORY_QUERIES.items():
        for q in queries:
            rows = await fetch_naver_category(
                category=category,
                query=q["query"],
                sub_category=q["sub_category"],
            )
            all_rows.extend(rows)
    return all_rows
