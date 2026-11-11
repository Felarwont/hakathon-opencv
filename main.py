import cv2, time, argparse
from detector import process_frame, draw
from geo import pixel_to_geo
from flight import AutoPilot
from telemetry import send_event, flush_buffer
from config import *

def main(simulation=True):
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    pilot = None
    if not simulation:
        pilot = AutoPilot()
        pilot.connect()
        pilot.arm_and_takeoff(DRONE_ALT_M)

    last_tx = {}   # дебаунс: не спамим одинаковыми событиями
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # --- телеметрия ---
            if pilot:
                t = pilot.telemetry()
                lat, lon = t["lat"], t["lon"]
                alt, hdg = t["alt"], t["heading"]
                battery = t["battery"]
            else:
                # заглушка для оффлайн-демо
                lat, lon, alt, hdg, battery = 55.7558, 37.6173, \
                                              DRONE_ALT_M, 0, 100

            # --- CV ---
            detections = process_frame(frame)
            frame = draw(frame, detections)

            # --- геопривязка + отправка ---
            flush_buffer()
            for d in detections:
                x, y, w, h = d["bbox"]
                cx, cy = x + w / 2, y + h / 2
                t_lat, t_lon = pixel_to_geo(cx, cy, FRAME_WIDTH,
                                            FRAME_HEIGHT, lat, lon,
                                            alt, hdg)
                key = (d["label"], round(t_lat, 4), round(t_lon, 4))
                now = time.time()
                if now - last_tx.get(key, 0) < 10:  # раз в 10 сек
                    continue
                last_tx[key] = now

                # send_event({
                #     "label": d["label"],
                #     "lat": t_lat,
                #     "lon": t_lon,
                #     "alt": alt,
                #     "drone_lat": lat,
                #     "drone_lon": lon,
                #     "bbox": d["bbox"],
                #     "battery": battery,
                # })

            cv2.imshow("OKO MCHS", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

            # авто-RTL при низком заряде
            if pilot and battery < 20:
                print("[MAIN] Низкий заряд — RTL")
                pilot.rtl()
                break
    finally:
        if pilot:
            pilot.rtl()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true",
                    help="Без подключения к дрону (только CV)")
    args = ap.parse_args()
    main(simulation=args.sim)