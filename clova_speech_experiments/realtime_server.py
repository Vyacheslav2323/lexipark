import os
import json
import threading
import queue
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import uvicorn
import grpc
from logger import log_error, log_tried, log_working


def _import_stubs():
    try:
        from clova_speech_experiments import nest_pb2_grpc as _pbg, nest_pb2 as _pb
        return _pb, _pbg
    except Exception:
        try:
            import nest_pb2_grpc as _pbg  # type: ignore
            import nest_pb2 as _pb  # type: ignore
            return _pb, _pbg
        except Exception:
            return None, None

def make_stub():
    try:
        _, pbg = _import_stubs()
        if pbg is None:
            return None
        u = os.getenv("CLOVA_SPEECH_GRPC_URL", "")
        c = grpc.secure_channel(u, grpc.ssl_channel_credentials())
        return pbg.NestServiceStub(c)
    except Exception:
        return None


def make_md():
    s = os.getenv("CLOVA_SPEECH_CLIENT_SECRET", "")
    return (("authorization", f"Bearer {s}"),)


def cfg_json():
    lang = os.getenv("CLOVA_SPEECH_LANGUAGE", "ko")
    return {"transcription": {"language": lang}}


def req_cfg():
    pb, _ = _import_stubs()
    if pb is None:
        raise RuntimeError("stubs missing")
    return pb.NestRequest(type=pb.RequestType.CONFIG, config=pb.NestConfig(config=json.dumps(cfg_json())))


def req_dat(chunk, seq, ep):
    pb, _ = _import_stubs()
    if pb is None:
        raise RuntimeError("stubs missing")
    return pb.NestRequest(type=pb.RequestType.DATA, data=pb.NestData(chunk=chunk, extra_contents=json.dumps({"seqId": seq, "epFlag": ep})))


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
    import sys, importlib, pkgutil, pathlib, traceback
    out = {"ok": True}
    try:
        import grpc  # type: ignore
        out["has_grpc"] = True
        out["grpc_version"] = getattr(grpc, "__version__", "unknown")
    except Exception as e:
        out["has_grpc"] = False
        out["grpc_error"] = repr(e)
    try:
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        stub_dir = repo_root / "clova_speech_experiments"
        out["stub_dir_exists"] = stub_dir.exists()
        out["stub_dir"] = str(stub_dir)
        if stub_dir.exists():
            out["stub_dir_ls"] = sorted(p.name for p in stub_dir.iterdir() if p.is_file())
        mod = importlib.import_module("clova_speech_experiments.nest_pb2")
        importlib.import_module("clova_speech_experiments.nest_pb2_grpc")
        out["has_stub"] = True
        out["stub_file"] = getattr(mod, "__file__", None)
    except Exception as e:
        out["has_stub"] = False
        out["stub_error"] = "".join(traceback.format_exception_only(type(e), e)).strip()
    out["cwd"] = os.getcwd()
    out["sys_path_head"] = sys.path[:6]
    out["packages_seen"] = [m.name for m in pkgutil.iter_modules() if m.name.startswith("clova")]
    out["has_token"] = bool(os.getenv("CLOVA_SPEECH_CLIENT_SECRET", ""))
    out["url_set"] = bool(os.getenv("CLOVA_SPEECH_GRPC_URL", ""))
    out["lang"] = os.getenv("CLOVA_SPEECH_LANGUAGE", "")
    return out


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


