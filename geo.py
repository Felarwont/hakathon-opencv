import math
from config import *

def pixel_to_geo(cx_px, cy_px, frame_w, frame_h,
                 drone_lat, drone_lon, drone_alt_m,
                 drone_heading_deg):
    """
    Приближённое геопозиционирование центра bbox.
    Работает для камеры, направленной вниз (nadir).
    """
    # смещение пикселя от центра кадра
    dx = cx_px - frame_w / 2
    dy = cy_px - frame_h / 2

    # углы в радианах на пиксель (по горизонтали)
    hfov_rad = math.radians(HFOV_DEG)
    fov_per_px_x = hfov_rad / frame_w
    fov_per_px_y = hfov_rad / frame_w  # соотношение сторон ≈ одинаковое

    # смещение в метрах на земле (упрощение: плоскость)
    ground_dx = drone_alt_m * math.tan(dx * fov_per_px_x)
    ground_dy = drone_alt_m * math.tan(dy * fov_per_px_y)

    # поворот на курс дрона
    hdg = math.radians(drone_heading_deg)
    east  =  ground_dx * math.cos(hdg) + ground_dy * math.sin(hdg)
    north = -ground_dx * math.sin(hdg) + ground_dy * math.cos(hdg)

    # перевод метров в градусы
    d_lat = north / 111320.0
    d_lon = east  / (111320.0 * math.cos(math.radians(drone_lat)))

    return drone_lat + d_lat, drone_lon + d_lon