
import cv2
import sqlite3
import time

from datetime import datetime
from ultralytics import YOLO

# YOLO model
model = YOLO("yolo11n.pt")

# Kamera
kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
kamera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Bazani tayyorlash
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

# Kuzatilayotgan avtomobillar
active_cars = {}

print("PARKING AI ISHGA TUSHDI!")
print("Avtomobillar kutilmoqda...")

while True:

    ret, frame = kamera.read()

    if not ret:
        print("Kamera bilan aloqa uzildi!")
        break

    # YOLO orqali avtomobilni aniqlash va kuzatish
    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[2, 3, 5, 7],
        conf=0.45,
        imgsz=416,
        verbose=False
    )

    current_time = time.time()

    for result in results:

        if result.boxes.id is None:
            continue

        boxes = result.boxes

        for box in boxes:

            track_id = int(box.id[0])
            sinf = int(box.cls[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            nom = model.names[sinf]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                nom,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Yangi avtomobilni bazaga yozish
            if track_id not in active_cars:

                vaqt = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                raqam = (
                    f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    f"-{track_id}"
                )

                db = sqlite3.connect("parking.db")
                cursor = db.cursor()

                cursor.execute(
                    """
                    INSERT INTO cars (number, entry_time)
                    VALUES (?, ?)
                    """,
                    (raqam, vaqt)
                )

                db.commit()
                db.close()

                print("-------------------------")
                print("YANGI AVTOMOBIL ANIQLANDI!")
                print("ID:", raqam)
                print("Vaqt:", vaqt)
                print("BAZAGA SAQLANDI!")
                print("-------------------------")

            active_cars[track_id] = current_time

    # 10 soniya ko'rinmagan avtomobilni kuzatuvdan chiqarish
    for track_id in list(active_cars):

        if current_time - active_cars[track_id] > 10:
            del active_cars[track_id]

    cv2.imshow("PARKING SYSTEM - KIRISH", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

kamera.release()
cv2.destroyAllWindows()

print("Parking kamerasi to'xtatildi!")
