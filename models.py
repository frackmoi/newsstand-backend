"""
SQLAlchemy ORM model for the articles table.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Index, UniqueConstraint
from database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Classification ─────────────────────────────────
    category = Column(
        String(20), nullable=False, index=True,
        comment="사회 | 경영경제 | 인사노무 | 글로벌",
    )
    sub_category = Column(
        String(30), nullable=True,
        comment="인사노무 전용: 핫이슈 | 법령/근로기준법 | 법령개정/판례",
    )

    # ── Content ────────────────────────────────────────
    title = Column(String(300), nullable=False)
    # String(500) instead of Text so PostgreSQL can enforce UNIQUE constraint
    link = Column(String(500), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # ── Dates ──────────────────────────────────────────
    pub_date = Column(DateTime, nullable=True, comment="기사 원본 발행일시")
    fetch_date = Column(
        Date, nullable=False, index=True,
        comment="수집 날짜 (YYYY-MM-DD, KST 기준)",
    )

    # ── Source ─────────────────────────────────────────
    source = Column(String(20), nullable=False, comment="naver | google")

    # ── Composite index + UNIQUE constraint ─────────────
    __table_args__ = (
        Index("ix_category_fetch", "category", "fetch_date"),
        UniqueConstraint("link", name="uq_articles_link"),
    )

    def __repr__(self):
        return f"<Article id={self.id} cat={self.category} title={self.title[:30]}>"
