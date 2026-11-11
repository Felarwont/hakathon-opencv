import cv2
import numpy as np
from ultralytics import YOLO

def detect_fire(frame):
    """
    Обнаружение пожара с помощью фильтрации по цвету в HSV-пространстве.
    Ищет яркие оттенки красного, оранжевого и желтого цветов.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Диапазон цветов огня в HSV
    lower_fire = np.array([0, 80, 100])
    upper_fire = np.array([35, 255, 255])
    
    mask = cv2.inRange(hsv, lower_fire, upper_fire)
    
    # Очистка шумов с помощью морфологических операций
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    fire_detected = False
    for c in contours:
        area = cv2.contourArea(c)
        if area > 100:  # Минимальная площадь для предотвращения ложных срабатываний
            fire_detected = True
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, "FIRE DETECTED!", (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
    return frame, fire_detected

def detect_flood(frame):
    """
    Обнаружение масштабного затопления по процентному соотношению 
    водных/размытых оттенков в кадре.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Диапазон для синей/мутной воды (можно калибровать под конкретное видео)
    lower_water = np.array([90, 50, 50])
    upper_water = np.array([130, 255, 255])
    
    mask = cv2.inRange(hsv, lower_water, upper_water)
    
    water_area = cv2.countNonZero(mask)
    total_area = frame.shape[0] * frame.shape[1]
    
    # Если вода занимает более 35% площади кадра — считаем это наводнением
    flood_detected = (water_area / total_area) > 0.35
    
    if flood_detected:
        cv2.putText(frame, "WARNING: FLOOD / WATERLOGGING!", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        
    return frame, flood_detected

def main():
    # Загружаем предобученную модель YOLOv8 (nano-версия для быстродействия)
    # При первом запуске она автоматически скачает файл весов yolov8n.pt (~6 МБ)
    model = YOLO('yolov8n.pt')
    
    # Путь к вашему видеофайлу для демонстрации (замените на свой файл)
    video_path = 'vk-mp4_360.mp4' 
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Ошибка: не удалось открыть видеофайл {video_path}")
        print("Пожалуйста, положите видео в папку с проектом или укажите правильный путь.")
        return

    print("Система мониторинга запущена. Нажмите 'q' для выхода.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Видео закончилось или недоступно.")
            break

        # Уменьшим разрешение кадра для ускорения обработки (опционально)
        frame = cv2.resize(frame, (1024, 576))

        # 1. Поиск пострадавших (людей) через YOLOv8
        # Класс 'person' имеет индекс 0 в стандартном датасете COCO
        results = model(frame, verbose=False)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Если это человек (класс 'person') и уверенность модели > 50%
                if model.names[cls_id] == 'person' and confidence > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Victim/Person {confidence:.2f}", (x1, max(y1 - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 2. Обнаружение пожара
        frame, fire_flag = detect_fire(frame)

        # 3. Обнаружение наводнения
        frame, flood_flag = detect_flood(frame)

        # Вывод обработанного кадра на экран
        cv2.imshow("Drone Disaster Monitoring System (Demo)", frame)

        # Выход по нажатию клавиши 'q'
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()