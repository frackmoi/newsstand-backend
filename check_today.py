import sqlite3
from datetime import date

db_path = 'c:/Users/minsu/.gemini/antigravity/scratch/newsstand/newsstand.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

today = '2026-03-15'
cursor.execute("SELECT category, COUNT(*) FROM articles WHERE fetch_date = ? GROUP BY category", (today,))
rows = cursor.fetchall()

print(f"--- Articles for {today} ---")
total = 0
for cat, count in rows:
    print(f"  {cat}: {count}")
    total += count
print(f"Total: {total}")

conn.close()
