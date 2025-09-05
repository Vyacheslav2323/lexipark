import os
from datetime import datetime

BASE = "/Users/slimslavik/Desktop/vorp_extra/clova_speech_experiments/logs"


def _write(name, msg):
    os.makedirs(BASE, exist_ok=True)
    path = os.path.join(BASE, name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} {msg}\n")
    return True


def log_error(msg):
    return _write("errors.log", msg)


def log_tried(msg):
    return _write("tried.log", msg)


def log_working(msg):
    return _write("working.log", msg)


