import sqlite3

def check_counts():
    conn = sqlite3.connect('newsstand.db')
    cursor = conn.cursor()
    
    print("--- Category Counts ---")
    cursor.execute("SELECT category, COUNT(*) FROM articles GROUP BY category")
    for cat, count in cursor.fetchall():
        print(f"  {cat}: {count}개")
        
    print("\n--- 글로벌 Sub-category Counts ---")
    cursor.execute("SELECT sub_category, COUNT(*) FROM articles WHERE category='글로벌' GROUP BY sub_category")
    for sub_cat, count in cursor.fetchall():
        print(f"  {sub_cat or '기타'}: {count}개")
        
    conn.close()

if __name__ == "__main__":
    check_counts()
