CAMERA_INDEX = 0            # или RTSP-поток с дрона
FRAME_WIDTH, FRAME_HEIGHT = 1280, 720
HFOV_DEG = 84.0             # горизонтальный угол обзора камеры
DRONE_ALT_M = 50.0          # рабочая высота
CONNECTION_STRING = "udp:127.0.0.1:14550"   # SITL / реальный дрон
SERVER_URL = "http://localhost:8000/api/events"  # куда шлём события

# Цветовые пороги HSV
FIRE_HSV_LOW  = [(0, 120, 180), (15, 120, 180)]   # оранжево-красный
FIRE_HSV_HIGH = [(15, 255, 255), (35, 255, 255)]  # жёлтый
WATER_HSV_LOW  = (90, 40, 40)      # сине-серый (вода/наводнение)
WATER_HSV_HIGH = (130, 255, 255)

MIN_CONTOUR_AREA = 3000