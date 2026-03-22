"""
FastAPI main application.

Serves the mobile newsstand UI and JSON API endpoints.
"""
import logging
import socket
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db, engine, Base
from models import Article
from scheduler import start_scheduler
from collector import run_collection

logger = logging.getLogger(__name__)

# ── Logging setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Lifespan: init DB + scheduler ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    # Start background scheduler
    sched = start_scheduler()
    
    # Print mobile access message
    local_ip = get_local_ip()
    print(f"\n[Mobile Access] http://{local_ip}:8000")
    print(f"[Local Access]  http://127.0.0.1:8000\n")
    
    yield
    logger.info("Scheduler shut down.")


app = FastAPI(title="Personal Newsstand", lifespan=lifespan)

# Add CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# ── Valid categories ───────────────────────────────────────────
VALID_CATEGORIES = {"사회", "경영경제", "인사노무", "글로벌"}


# ── Helper: resolve date ──────────────────────────────────────
def _resolve_date(date_str: str | None) -> date | None:
    """Parse a YYYY-MM-DD string or fall back to today only if no date_str provided."""
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    # KST is UTC+9
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date()


# ── Routes ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main mobile newsstand page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/manifest.json")
async def get_manifest():
    """Serve the web app manifest."""
    return FileResponse("manifest.json", media_type="application/manifest+json")


@app.get("/service-worker.js")
async def get_service_worker():
    """Serve the service worker."""
    return FileResponse("service-worker.js", media_type="application/javascript")


@app.get("/api/news")
def get_daily_news(
    date: str = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Return top 3 articles per category for the given date.
    Strictly filters by pub_date matching requested date.
    """
    target = _resolve_date(date)
    if not target:
        return {"date": date, "categories": {cat: [] for cat in VALID_CATEGORIES}}

    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date()
    if target == today_kst and db.query(Article).filter(Article.fetch_date == target).count() == 0:
        logger.info("Auto-fetching news for today...")
        run_collection()

    result: dict[str, list] = {}

    for cat in VALID_CATEGORIES:
        articles = (
            db.query(Article)
            .filter(Article.fetch_date == target, Article.category == cat)
            .order_by(Article.pub_date.desc(), Article.id.desc())
            .limit(3)
            .all()
        )
        result[cat] = [_article_dict(a) for a in articles]

    return {"date": str(target), "categories": result}


@app.get("/api/mobile/news")
def get_mobile_news(
    date: str = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Return a flat list of recent articles formatted for the mobile app, filtered by date.
    """
    target = _resolve_date(date)
    if not target:
        return []

    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date()
    if target == today_kst and db.query(Article).filter(Article.fetch_date == target).count() == 0:
        logger.info("Auto-fetching news for today...")
        run_collection()

    articles = (
        db.query(Article)
        .filter(Article.fetch_date == target)
        .order_by(Article.pub_date.desc())
        .limit(30)
        .all()
    )
    
    result = []
    for a in articles:
        # Use a placeholder image if imageUrl isn't scraped
        image_url = f"https://picsum.photos/seed/news_{a.id}/600/300"
        
        result.append({
            "id": str(a.id),
            "title": a.title,
            "summary": a.description if a.description else "No summary available.",
            "imageUrl": image_url,
            "url": a.link,
            "publishedAt": str(a.pub_date) if a.pub_date else str(a.fetch_date),
        })
        
    return result


@app.get("/api/news/{category}")
def get_category_news(
    category: str,
    date: str = Query(None, description="YYYY-MM-DD"),
    sub_category: str = Query(None, description="Sub-category filter"),
    db: Session = Depends(get_db),
):
    """
    Return up to 10 articles for a specific category on a date.
    For 인사노무, optionally filter by sub_category.
    """
    target = _resolve_date(date)

    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date()
    if target == today_kst and db.query(Article).filter(Article.fetch_date == target).count() == 0:
        logger.info("Auto-fetching news for today...")
        run_collection()

    query = (
        db.query(Article).filter(Article.fetch_date == target, Article.category == category)
    )

    if sub_category:
        query = query.filter(Article.sub_category == sub_category)

    articles = query.order_by(Article.pub_date.desc(), Article.id.desc()).limit(50).all()

    return {
        "date": str(target),
        "category": category,
        "sub_category": sub_category,
        "articles": [_article_dict(a) for a in articles],
    }


@app.get("/api/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/collect")
def trigger_collection():
    """Manual trigger for news collection (for testing)."""
    summary = run_collection()
    return summary


@app.get("/api/dates")
def get_available_dates(db: Session = Depends(get_db)):
    """Return list of dates that have articles in the DB."""
    rows = (
        db.query(Article.fetch_date)
        .distinct()
        .order_by(Article.fetch_date.desc())
        .all()
    )
    return {"dates": [str(r[0]) for r in rows]}


# ── Serializer ─────────────────────────────────────────────────
def _article_dict(a: Article) -> dict:
    return {
        "id": a.id,
        "category": a.category,
        "sub_category": a.sub_category,
        "title": a.title,
        "link": a.link,
        "description": a.description,
        "pub_date": str(a.pub_date) if a.pub_date else None,
        "source": a.source,
    }


def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == "__main__":
    import uvicorn
    import os
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 8889))
    uvicorn.run(app, host="0.0.0.0", port=port)
