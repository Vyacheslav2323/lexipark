import os
import json
import threading
import queue
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import uvicorn
import grpc
from logger import log_error, log_tried, log_working


def make_stub():
    try:
        import nest_pb2_grpc
        u = os.getenv("CLOVA_SPEECH_GRPC_URL", "")
        c = grpc.secure_channel(u, grpc.ssl_channel_credentials())
        return nest_pb2_grpc.NestServiceStub(c)
    except Exception:
        return None


def make_md():
    s = os.getenv("CLOVA_SPEECH_CLIENT_SECRET", "")
    return (("authorization", f"Bearer {s}"),)


def cfg_json():
    lang = os.getenv("CLOVA_SPEECH_LANGUAGE", "ko")
    return {"transcription": {"language": lang}}


def req_cfg():
    import nest_pb2
    return nest_pb2.NestRequest(type=nest_pb2.RequestType.CONFIG, config=nest_pb2.NestConfig(config=json.dumps(cfg_json())))


def req_dat(chunk, seq, ep):
    import nest_pb2
    return nest_pb2.NestRequest(type=nest_pb2.RequestType.DATA, data=nest_pb2.NestData(chunk=chunk, extra_contents=json.dumps({"seqId": seq, "epFlag": ep})))


def iter_requests(aq, stop):
    yield req_cfg()
    i = 0
    while not stop.is_set():
        try:
            b = aq.get(timeout=0.1)
            if b is None:
                break
            yield req_dat(b, i, False)
            i += 1
        except queue.Empty:
            continue
    yield req_dat(b"", i, True)


def run_grpc(aq, rq, stop):
    log_tried("realtime grpc start")
    try:
        stub = make_stub()
        md = make_md()
        has_token = bool(md and md[0][1].split()[-1])
        if not stub or not has_token:
            log_error("realtime missing cfg")
            try:
                rq.put_nowait(json.dumps({"type":"error","message":"missing cfg: stub or token"}))
            except Exception:
                pass
            stop.set()
            return False
        m = getattr(stub, "Recognize", None) or getattr(stub, "recognize", None)
        for r in m(iter_requests(aq, stop), metadata=md):
            try:
                rq.put_nowait(json.dumps({"type": "resp", "data": getattr(r, "contents", "")}))
            except Exception:
                continue
        log_working("realtime grpc done")
        return True
    except Exception as e:
        log_error(f"realtime grpc err {e}")
        try:
            rq.put_nowait(json.dumps({"type":"error","message":str(e)}))
        except Exception:
            pass
        stop.set()
        return False


app = FastAPI()


@app.get("/")
def index():
    p = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(p)

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    aq = queue.Queue(maxsize=128)
    rq = queue.Queue(maxsize=128)
    stop = threading.Event()
    t = threading.Thread(target=run_grpc, args=(aq, rq, stop), daemon=True)
    t.start()
    try:
        while not stop.is_set():
            try:
                m = await ws.receive_bytes()
                aq.put_nowait(m)
            except Exception:
                break
            try:
                o = rq.get_nowait()
                await ws.send_text(o)
            except queue.Empty:
                pass
    finally:
        stop.set()
        try:
            await ws.close()
        except Exception:
            pass


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/diag")
def diag():
    try:
        u = os.getenv("CLOVA_SPEECH_GRPC_URL", "")
        s = os.getenv("CLOVA_SPEECH_CLIENT_SECRET", "")
        lang = os.getenv("CLOVA_SPEECH_LANGUAGE", "")
        return {"ok": True, "has_stub": make_stub() is not None, "has_token": bool(s), "lang": lang, "url_set": bool(u)}
    except Exception:
        return {"ok": False}


def main():
    host = "0.0.0.0"
    try:
        port = int(os.getenv("PORT", "8081"))
    except Exception:
        port = 8081
    uvicorn.run(app, host=host, port=port, reload=False)
    return True


if __name__ == "__main__":
    main()


