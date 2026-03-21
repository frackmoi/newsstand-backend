import sqlite3

conn = sqlite3.connect("newsstand.db")

rows = conn.execute(
    "SELECT id, category, sub_category, title, source, fetch_date FROM articles LIMIT 5"
).fetchall()

for r in rows:
    print(r)

total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
print(f"\nTotal articles: {total}")

conn.close()
