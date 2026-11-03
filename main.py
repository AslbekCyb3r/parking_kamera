
import sqlite3
from datetime import datetime
import math

SOATLIK_NARX = 5000


def mashina_kirdi():
    raqam = input("Mashina raqami: ").upper().strip()
    vaqt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = sqlite3.connect("parking.db")
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO cars (number, entry_time) VALUES (?, ?)",
        (raqam, vaqt)
    )

    db.commit()
    db.close()

    print("Mashina muvaffaqiyatli kirdi!")


def mashina_chiqdi():
    raqam = input("Mashina raqami: ").upper().strip()

    db = sqlite3.connect("parking.db")
    cursor = db.cursor()

    cursor.execute(
        """SELECT id, entry_time FROM cars
        WHERE number = ? AND exit_time IS NULL
        ORDER BY id DESC LIMIT 1""",
        (raqam,)
    )

    mashina = cursor.fetchone()

    if mashina is None:
        print("Mashina topilmadi!")
        db.close()
        return

    mashina_id, kirish_vaqti = mashina

    kirish = datetime.strptime(kirish_vaqti, "%Y-%m-%d %H:%M:%S")
    chiqish = datetime.now()

    daqiqa = (chiqish - kirish).total_seconds() / 60
    soat = max(1, math.ceil(daqiqa / 60))
    pul = soat * SOATLIK_NARX

    cursor.execute(
        "UPDATE cars SET exit_time=?, price=? WHERE id=?",
        (chiqish.strftime("%Y-%m-%d %H:%M:%S"), pul, mashina_id)
    )

    db.commit()
    db.close()

    print("Mashina chiqdi!")
    print("Turish vaqti:", round(daqiqa, 2), "daqiqa")
    print("To'lov:", pul, "so'm")


def parkingdagi_mashinalar():
    db = sqlite3.connect("parking.db")
    cursor = db.cursor()

    cursor.execute(
        "SELECT number, entry_time FROM cars WHERE exit_time IS NULL"
    )

    mashinalar = cursor.fetchall()

    print("\n--- PARKINGDAGI MASHINALAR ---")

    for raqam, vaqt in mashinalar:
        print(raqam, "-", vaqt)

    if not mashinalar:
        print("Parking bo'sh!")

    db.close()


def daromad():
    db = sqlite3.connect("parking.db")
    cursor = db.cursor()

    cursor.execute(
        "SELECT SUM(price) FROM cars WHERE DATE(exit_time) = DATE('now', 'localtime')"
    )

    jami = cursor.fetchone()[0]

    print("Bugungi daromad:", jami or 0, "so'm")

    db.close()


while True:
    print("\n====== PARKING SYSTEM ======")
    print("1. Mashina kiritish")
    print("2. Mashina chiqarish")
    print("3. Parkingdagi mashinalar")
    print("4. Bugungi daromad")
    print("0. Chiqish")

    tanlov = input("Tanlang: ")

    if tanlov == "1":
        mashina_kirdi()
    elif tanlov == "2":
        mashina_chiqdi()
    elif tanlov == "3":
        parkingdagi_mashinalar()
    elif tanlov == "4":
        daromad()
    elif tanlov == "0":
        print("Dastur yopildi!")
        break
    else:
        print("Noto'g'ri tanlov!")
