
import cv2
from ultralytics import YOLO

model = YOLO("yolo11n.pt")

kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

kamera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = kamera.read()

    if not ret:
        break

    natija = model(frame, imgsz=416, verbose=False)

    for result in natija:
        for box in result.boxes:
            sinf = int(box.cls[0])

            # 2 = car, 3 = motorcycle,
            # 5 = bus, 7 = truck
            if sinf in [2, 3, 5, 7]:
                x1, y1, x2, y2 = map(
                    int, box.xyxy[0]
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                nom = model.names[sinf]

                cv2.putText(
                    frame,
                    nom,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

    cv2.imshow("PARKING AI", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

kamera.release()
cv2.destroyAllWindows()
