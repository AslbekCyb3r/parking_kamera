
import sqlite3

db = sqlite3.connect("parking.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT,
    entry_time TEXT,
    exit_time TEXT,
    price INTEGER
)
""")

db.commit()
db.close()

print("Parking bazasi tayyor!")
