import os
import json
import argparse
from logger import log_error, log_tried, log_working


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("audio", nargs="+")
    a = p.parse_args()
    return " ".join(a.audio)


def get_lang():
    x = os.getenv("CLOVA_SPEECH_LANGUAGE", "ko")
    return x


def make_metadata():
    s = os.getenv("CLOVA_SPEECH_CLIENT_SECRET", "")
    return (("authorization", f"Bearer {s}"),)


def make_stub():
    try:
        import grpc
        import nest_pb2_grpc
        u = os.getenv("CLOVA_SPEECH_GRPC_URL", "")
        c = grpc.secure_channel(u, grpc.ssl_channel_credentials())
        return nest_pb2_grpc.NestServiceStub(c)
    except Exception:
        return None


def request_config(lang):
    import nest_pb2
    return nest_pb2.NestRequest(type=nest_pb2.RequestType.CONFIG, config=nest_pb2.NestConfig(config=json.dumps({"transcription": {"language": lang}})))


def request_data(chunk, seq, ep):
    import nest_pb2
    return nest_pb2.NestRequest(type=nest_pb2.RequestType.DATA, data=nest_pb2.NestData(chunk=chunk, extra_contents=json.dumps({"seqId": seq, "epFlag": ep})))


def make_streamer(lang):
    def _gen(a):
        yield request_config(lang)
        with open(a, "rb") as f:
            i = 0
            while True:
                b = f.read(32000)
                if not b:
                    break
                yield request_data(b, i, False)
                i += 1
        yield request_data(b"", i, True)
    return _gen


def transcribe_grpc(audio_path):
    log_tried(f"transcribe_grpc {audio_path}")
    try:
        stub = make_stub()
        md = make_metadata()
        lang = get_lang()
        if not stub or not md[0][1].split()[-1]:
            log_error(f"transcribe_grpc {audio_path} missing cfg")
            return {"ok": False, "text": "", "status": -1}
        m = getattr(stub, "Recognize", None) or getattr(stub, "recognize", None)
        if not m:
            log_error(f"transcribe_grpc {audio_path} no method")
            return {"ok": False, "text": "", "status": -1}
        s = make_streamer(lang)
        out = []
        for r in m(s(audio_path), metadata=md):
            v = getattr(r, "contents", "") or getattr(r, "result", "")
            if v:
                out.append(v)
        t = "".join(out)
        if not t:
            log_error(f"transcribe_grpc {audio_path} empty")
            return {"ok": False, "text": "", "status": 204}
        log_working(f"transcribe_grpc {audio_path}")
        return {"ok": True, "text": t, "status": 200}
    except Exception as e:
        log_error(f"transcribe_grpc {audio_path} {e}")
        return {"ok": False, "text": "", "status": -1}


def main(audio_path):
    r = transcribe_grpc(audio_path)
    if not r.get("ok"):
        print("")
        return 1
    print(r.get("text", ""))
    return 0


if __name__ == "__main__":
    p = parse_args()
    raise SystemExit(main(p))



