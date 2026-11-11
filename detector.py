import cv2
import numpy as np
from config import *

def detect_fire(frame_bgr):
    """Детекция открытого огня/дыма по цвету + форме."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

    for low, high in zip(FIRE_HSV_LOW, FIRE_HSV_HIGH):
        mask |= cv2.inRange(hsv, np.array(low), np.array(high))

    # морфология для устранения шума
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) < MIN_CONTOUR_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        # фильтр по форме: огонь обычно вертикально вытянут
        if h / max(w, 1) < 0.5:
            continue
        boxes.append({"label": "fire", "bbox": (x, y, w, h),
                      "area": int(cv2.contourArea(c))})
    return boxes


def detect_water(frame_bgr):
    """Детекция воды/наводнения по цвету и горизонтальности области."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(WATER_HSV_LOW),
                            np.array(WATER_HSV_HIGH))
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) < MIN_CONTOUR_AREA * 3:
            continue
        x, y, w, h = cv2.boundingRect(c)
        # вода растекается горизонтально
        if w / max(h, 1) < 1.2:
            continue
        boxes.append({"label": "flood", "bbox": (x, y, w, h),
                      "area": int(cv2.contourArea(c))})
    return boxes


# --- Опционально: люди / пострадавшие (YOLOv8) ---
_person_model = None
def detect_people(frame_bgr):
    """Требует: pip install ultralytics."""
    global _person_model
    if _person_model is None:
        from ultralytics import YOLO
        _person_model = YOLO("yolov8n.pt")
    results = _person_model(frame_bgr, classes=[0], verbose=False)  # class 0 = person
    boxes = []
    for r in results:
        for b in r.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            boxes.append({"label": "person",
                          "bbox": (x1, y1, x2 - x1, y2 - y1),
                          "conf": float(b.conf[0])})
    return boxes


def process_frame(frame_bgr):
    """Объединяет все детекторы."""
    detections = []
    detections += detect_fire(frame_bgr)
    detections += detect_water(frame_bgr)
    try:
        detections += detect_people(frame_bgr)
    except Exception:
        pass  # YOLO не установлен — пропускаем
    return detections


def draw(frame_bgr, detections):
    for d in detections:
        x, y, w, h = d["bbox"]
        color = {"fire": (0, 0, 255),
                 "flood": (255, 128, 0),
                 "person": (0, 255, 0)}.get(d["label"], (255, 255, 255))
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame_bgr, d["label"], (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame_bgr