import os
import argparse
import requests
from logger import log_error, log_tried, log_working


def transcribe(audio_path):
    log_tried(f"transcribe {audio_path}")
    try:
        url = os.getenv("CLOVA_SPEECH_URL", "")
        cid = os.getenv("CLOVA_SPEECH_CLIENT_ID", "")
        csec = os.getenv("CLOVA_SPEECH_CLIENT_SECRET", "")
        with open(audio_path, "rb") as f:
            r = requests.post(url, headers={"X-NCP-APIGW-API-KEY-ID": cid, "X-NCP-APIGW-API-KEY": csec}, files={"media": f})
        if r.status_code != 200:
            log_error(f"transcribe {audio_path} {r.status_code} {r.text}")
            return {"ok": False, "text": "", "status": r.status_code}
        log_working(f"transcribe {audio_path}")
        return {"ok": True, "text": r.text, "status": 200}
    except Exception as e:
        log_error(f"transcribe {audio_path} {e}")
        return {"ok": False, "text": "", "status": -1}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("audio", nargs="+")
    a = p.parse_args()
    return " ".join(a.audio)


def main(audio_path):
    r = transcribe(audio_path)
    if not r.get("ok"):
        print("")
        return 1
    print(r.get("text", ""))
    return 0


if __name__ == "__main__":
    path = parse_args()
    raise SystemExit(main(path))



