"""Debug: Test raw Naver queries for 경영/경제/비즈니스"""
import asyncio
import httpx
from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

NAVER_URL = "https://openapi.naver.com/v1/search/news.json"

queries = [
    "기업 경영 -연예 -방송 -아이돌",
    "산업 경제 -연예 -방송 -아이돌",
    "비즈니스 전략 -연예 -방송 -아이돌",
    "증시 시황 -연예 -방송 -아이돌",
    "부동산 시장 -연예 -방송 -아이돌",
]


async def main():
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        for q in queries:
            resp = await client.get(
                NAVER_URL,
                headers=headers,
                params={"query": q, "display": 5, "start": 1, "sort": "date"},
            )
            data = resp.json()
            total = data.get("total", 0)
            items = data.get("items", [])
            print(f"Query: '{q}'  -> total={total}, returned={len(items)}")
            for it in items[:2]:
                title = it.get('title', '').replace('<b>', '').replace('</b>', '')
                pub_date = it.get('pubDate', '')
                print(f"  - [{pub_date}] {title[:60]}")
            print()


asyncio.run(main())
