
import sys
import sqlite3
import cv2

from pathlib import Path
from datetime import datetime
from math import ceil

from ultralytics import YOLO

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QMessageBox
)

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from regions import get_region


DB_PATH = Path(__file__).resolve().parent / "parking.db"

# Soatlik tariflar
RATES = {
    "motorcycle": 3000,
    "car": 5000,
    "bus": 10000,
    "truck": 15000
}

VEHICLE_NAMES = {
    "motorcycle": "Mototsikl",
    "car": "Yengil avtomobil",
    "bus": "Avtobus",
    "truck": "Yuk mashinasi"
}


class ParkingAdmin(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PARKING SYSTEM - ADMIN")
        self.resize(1350, 900)

        self.camera = None
        self.model = None
        self.detected_track_ids = set()

        self.prepare_database()
        self.create_ui()
        self.load_model()
        self.start_camera()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(150)

        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.update_data)
        self.data_timer.start(3000)

        self.update_data()

    # =====================================
    # DATABASE
    # =====================================

    def prepare_database(self):

        conn = sqlite3.connect(DB_PATH)

        try:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    price INTEGER
                )
            """)

            cursor.execute("PRAGMA table_info(cars)")
            columns = [
                column[1] for column in cursor.fetchall()
            ]

            if "region" not in columns:
                cursor.execute("""
                    ALTER TABLE cars ADD COLUMN region TEXT
                """)

            if "vehicle_type" not in columns:
                cursor.execute("""
                    ALTER TABLE cars
                    ADD COLUMN vehicle_type TEXT DEFAULT 'car'
                """)

            conn.commit()

        finally:
            conn.close()

    # =====================================
    # INTERFACE
    # =====================================

    def create_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        title = QLabel("PARKING SYSTEM")
        title.setObjectName("title")
        main_layout.addWidget(title)

        stats_layout = QHBoxLayout()

        self.active_label = self.create_card(
            stats_layout, "Parkingdagi mashinalar", "0"
        )

        self.today_label = self.create_card(
            stats_layout, "Bugun kirgan", "0"
        )

        self.money_label = self.create_card(
            stats_layout, "Bugungi daromad", "0 so'm"
        )

        main_layout.addLayout(stats_layout)

        # TARIFLAR
        rates_label = QLabel(
            "TARIFLAR: Mototsikl 3 000 | Yengil 5 000 | "
            "Avtobus 10 000 | Yuk mashinasi 15 000 so'm/soat"
        )
        rates_label.setStyleSheet("color: #38bdf8;")
        main_layout.addWidget(rates_label)

        # KAMERA
        main_layout.addWidget(QLabel("JONLI KAMERA"))

        self.camera_label = QLabel("Kamera ulanmoqda...")
        self.camera_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.camera_label.setMinimumHeight(330)
        self.camera_label.setStyleSheet(
            "background-color: black; border-radius: 10px;"
        )
        main_layout.addWidget(self.camera_label)

        self.status_label = QLabel("Kamera tekshirilmoqda...")
        main_layout.addWidget(self.status_label)

        self.yolo_status = QLabel("YOLO tekshirilmoqda...")
        main_layout.addWidget(self.yolo_status)

        # JADVAL
        main_layout.addWidget(QLabel("MASHINALAR TARIXI"))

        self.table = QTableWidget()
        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Raqam",
            "Transport turi",
            "Viloyat",
            "Kirish vaqti",
            "Chiqish vaqti",
            "To'lov"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        main_layout.addWidget(self.table)

        # TUGMALAR
        buttons = QHBoxLayout()

        refresh_btn = QPushButton("Yangilash")
        refresh_btn.clicked.connect(self.update_data)

        checkout_btn = QPushButton("Tanlangan mashinani chiqarish")
        checkout_btn.clicked.connect(self.checkout_selected)

        exit_btn = QPushButton("Chiqish")
        exit_btn.clicked.connect(self.close)

        buttons.addWidget(refresh_btn)
        buttons.addWidget(checkout_btn)
        buttons.addWidget(exit_btn)

        main_layout.addLayout(buttons)

    def create_card(self, layout, title, value):

        card = QFrame()
        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #38bdf8;
        """)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        layout.addWidget(card)

        return value_label

    # =====================================
    # YOLO
    # =====================================

    def load_model(self):

        try:
            self.yolo_status.setText("YOLO yuklanmoqda...")
            QApplication.processEvents()

            self.model = YOLO("yolo11n.pt")

            self.yolo_status.setText(
                "YOLO ONLINE - Transport aniqlash tayyor"
            )

        except Exception as error:
            self.model = None
            self.yolo_status.setText("YOLO xatosi")
            print("YOLO xatosi:", error)

    # =====================================
    # KAMERA
    # =====================================

    def start_camera(self):

        self.camera = cv2.VideoCapture(
            0, cv2.CAP_DSHOW
        )

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 15)

        if self.camera.isOpened():
            self.status_label.setText("KAMERA ONLINE")
        else:
            self.status_label.setText("KAMERA OFFLINE")

    # =====================================
    # TRANSPORTNI BAZAGA YOZISH
    # =====================================

    def save_detected_car(self, track_id, vehicle_type):

        conn = None

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            entry_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            car_number = (
                f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                f"-{track_id}"
            )

            region = get_region(car_number)

            cursor.execute("""
                INSERT INTO cars (
                    number, entry_time, exit_time,
                    price, region, vehicle_type
                )
                VALUES (?, ?, NULL, NULL, ?, ?)
            """, (
                car_number,
                entry_time,
                region,
                vehicle_type
            ))

            conn.commit()

            print(
                "TRANSPORT SAQLANDI:",
                car_number,
                VEHICLE_NAMES.get(vehicle_type, vehicle_type)
            )

            self.update_data()

        except sqlite3.Error as error:
            print("Database xatosi:", error)

        finally:
            if conn is not None:
                conn.close()

    # =====================================
    # KAMERA + YOLO ANIQLASH
    # =====================================

    def update_camera(self):

        if self.camera is None or not self.camera.isOpened():
            return

        success, frame = self.camera.read()

        if not success:
            return

        if self.model is not None:

            try:
                results = self.model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=[2, 3, 5, 7],
                    conf=0.45,
                    imgsz=416,
                    verbose=False
                )

                result = results[0]

                if (
                    result.boxes is not None
                    and result.boxes.id is not None
                ):

                    track_ids = (
                        result.boxes.id.int().cpu().tolist()
                    )

                    class_ids = (
                        result.boxes.cls.int().cpu().tolist()
                    )

                    for track_id, class_id in zip(
                        track_ids, class_ids
                    ):

                        vehicle_type = {
                            2: "car",
                            3: "motorcycle",
                            5: "bus",
                            7: "truck"
                        }.get(class_id)

                        if (
                            vehicle_type
                            and track_id not in self.detected_track_ids
                        ):

                            self.detected_track_ids.add(track_id)

                            self.save_detected_car(
                                track_id,
                                vehicle_type
                            )

                frame = result.plot()

            except Exception as error:
                print("YOLO aniqlash xatosi:", error)

        frame = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        height, width, channels = frame.shape

        image = QImage(
            frame.data,
            width,
            height,
            channels * width,
            QImage.Format.Format_RGB888
        ).copy()

        pixmap = QPixmap.fromImage(image)

        self.camera_label.setPixmap(
            pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    # =====================================
    # CHIQISH VA TO'LOV HISOBLASH
    # =====================================

    def checkout_selected(self):

        selected = self.table.currentRow()

        if selected < 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Avval jadvaldan mashinani tanlang!"
            )
            return

        car_id_item = self.table.item(selected, 0)

        if car_id_item is None:
            return

        car_id = int(car_id_item.text())

        conn = None

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT entry_time, exit_time, vehicle_type
                FROM cars
                WHERE id = ?
            """, (car_id,))

            car = cursor.fetchone()

            if car is None:
                QMessageBox.warning(
                    self, "Xato", "Mashina topilmadi!"
                )
                return

            entry_time, exit_time, vehicle_type = car

            if exit_time is not None:
                QMessageBox.information(
                    self,
                    "Ma'lumot",
                    "Bu mashina avval chiqarilgan!"
                )
                return

            entry = datetime.strptime(
                entry_time, "%Y-%m-%d %H:%M:%S"
            )

            exit_dt = datetime.now()

            # To'liq bo'lmagan daqiqa ham bir daqiqa hisoblanadi
            seconds = max(
                0,
                (exit_dt - entry).total_seconds()
            )

            minutes = max(1, ceil(seconds / 60))

            rate = RATES.get(vehicle_type, RATES["car"])

            # Daqiqaga qarab hisoblash
            price = int(rate * minutes / 60 + 0.5)

            exit_time_text = exit_dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                UPDATE cars
                SET exit_time = ?, price = ?
                WHERE id = ?
            """, (
                exit_time_text,
                price,
                car_id
            ))

            conn.commit()

            duration_hours = minutes // 60
            duration_minutes = minutes % 60

            QMessageBox.information(
                self,
                "To'lov hisoblandi",
                f"Transport: {VEHICLE_NAMES.get(vehicle_type, vehicle_type)}\n"
                f"Turgan vaqti: {duration_hours} soat "
                f"{duration_minutes} daqiqa\n"
                f"Soatlik tarif: {rate:,} so'm\n"
                f"Jami to'lov: {price:,} so'm"
            )

            self.update_data()

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.critical(
                self, "Xato", str(error)
            )

        finally:
            if conn is not None:
                conn.close()

    # =====================================
    # STATISTIKA VA JADVAL
    # =====================================

    def update_data(self):

        conn = None

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            today = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT COUNT(*)
                FROM cars
                WHERE exit_time IS NULL
            """)
            active = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM cars
                WHERE entry_time LIKE ?
            """, (today + "%",))
            today_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(price), 0)
                FROM cars
                WHERE exit_time LIKE ?
            """, (today + "%",))
            money = cursor.fetchone()[0]

            cursor.execute("""
                SELECT id, number, vehicle_type, region,
                       entry_time, exit_time, price
                FROM cars
                ORDER BY id DESC
                LIMIT 100
            """)

            rows = cursor.fetchall()

            self.active_label.setText(str(active))
            self.today_label.setText(str(today_count))
            self.money_label.setText(f"{money:,} so'm")

            self.table.setRowCount(len(rows))

            for row_index, row in enumerate(rows):

                for col_index, value in enumerate(row):

                    if col_index == 2:
                        value = VEHICLE_NAMES.get(
                            value, value or "Noma'lum"
                        )

                    item = QTableWidgetItem(
                        str(value) if value is not None else "-"
                    )

                    self.table.setItem(
                        row_index, col_index, item
                    )

        except sqlite3.Error as error:
            print("Database xatosi:", error)

        finally:
            if conn is not None:
                conn.close()

    # =====================================
    # DASTUR YOPILISHI
    # =====================================

    def closeEvent(self, event):

        self.timer.stop()
        self.data_timer.stop()

        if self.camera is not None:
            self.camera.release()

        event.accept()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ParkingAdmin()
    window.show()

    sys.exit(app.exec())
