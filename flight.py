from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
from config import *

class AutoPilot:
    def __init__(self):
        self.vehicle = None

    def connect(self):
        print("[FLIGHT] Подключение к дрону...")
        self.vehicle = connect(CONNECTION_STRING, wait_ready=True,
                               timeout=60)
        print("[FLIGHT] OK:", self.vehicle.version)

    def arm_and_takeoff(self, alt):
        v = self.vehicle
        while not v.is_armable:
            time.sleep(1)
        v.mode = VehicleMode("GUIDED")
        v.armed = True
        while not v.armed:
            time.sleep(1)
        v.simple_takeoff(alt)
        while True:
            if v.location.global_relative_frame.alt >= alt * 0.95:
                break
            time.sleep(1)
        print(f"[FLIGHT] Взлёт на {alt} м выполнен")

    def goto(self, lat, lon, alt):
        loc = LocationGlobalRelative(lat, lon, alt)
        self.vehicle.simple_goto(loc, groundspeed=8)

    def rtl(self):
        print("[FLIGHT] Возврат на базу (RTL)")
        self.vehicle.mode = VehicleMode("RTL")

    def land(self):
        self.vehicle.mode = VehicleMode("LAND")

    def telemetry(self):
        v = self.vehicle
        return {
            "lat": v.location.global_relative_frame.lat,
            "lon": v.location.global_relative_frame.lon,
            "alt": v.location.global_relative_frame.alt,
            "heading": v.heading,
            "battery": v.battery.level,
        }