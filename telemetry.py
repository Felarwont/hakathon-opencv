import requests, json, os, datetime
from config import SERVER_URL

def send_event(event: dict):
    payload = {
        **event,
        "ts": datetime.datetime.utcnow().isoformat() + "Z"
    }
    try:
        r = requests.post(SERVER_URL, json=payload, timeout=5)
        print(f"[TX] {r.status_code} → {event['label']} @ "
              f"{event['lat']:.6f},{event['lon']:.6f}")
    except Exception as e:
        # оффлайн — сохраняем в буфер
        os.makedirs("buffer", exist_ok=True)
        fn = f"buffer/{datetime.datetime.utcnow().timestamp()}.json"
        with open(fn, "w") as f:
            json.dump(payload, f)
        print(f"[TX] offline, saved {fn} ({e})")


def flush_buffer():
    """Отправка накопленных событий при появлении связи."""
    if not os.path.isdir("buffer"):
        return
    for fn in list(os.listdir("buffer")):
        path = os.path.join("buffer", fn)
        with open(path) as f:
            payload = json.load(f)
        try:
            requests.post(SERVER_URL, json=payload, timeout=5)
            os.remove(path)
        except Exception:
            return  # связи всё ещё нет