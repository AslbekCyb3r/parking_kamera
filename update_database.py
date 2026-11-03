
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "parking.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Jadval ustunlarini tekshirish
cursor.execute("PRAGMA table_info(cars)")
columns = [column[1] for column in cursor.fetchall()]

# Agar region ustuni bo'lmasa, qo'shish
if "region" not in columns:
    cursor.execute("""
        ALTER TABLE cars
        ADD COLUMN region TEXT
    """)
    print("Viloyat ustuni qo'shildi!")
else:
    print("Viloyat ustuni avvaldan mavjud!")

conn.commit()
conn.close()

print("Parking bazasi yangilandi!")
