import os
import sys
import json
import time
import wave
import queue
import grpc
import argparse
import sounddevice as sd

import nest_pb2 as pb
import nest_pb2_grpc as pbg

HOSTPORT = os.getenv('CLOVA_GRPC', 'clovaspeech-gw.ncloud.com:50051')
API_KEY = os.getenv('CLOVASPEECH_API_KEY')
LANG = os.getenv('CLOVA_LANG', 'ko-KR')

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 40
FRAMES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_MS / 1000)

def build_config_json():
    cfg = {
        'language': LANG,
        'sampleRate': SAMPLE_RATE,
        'encoding': 'LINEAR16',
        'interimResults': True,
    }
    return json.dumps(cfg, ensure_ascii=False)

def mic_request_iter():
    yield pb.NestRequest(type=pb.CONFIG, config=pb.NestConfig(config=build_config_json()))
    q = queue.Queue()
    def _cb(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        pcm16 = (indata[:, 0] * 32767.0).astype('<i2').tobytes()
        q.put(pcm16)
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=FRAMES_PER_CHUNK, callback=_cb):
        print('mic streaming… Ctrl+C to stop')
        try:
            while True:
                chunk = q.get()
                if chunk is None:
                    break
                yield pb.NestRequest(type=pb.DATA, data=pb.NestData(chunk=chunk))
        except KeyboardInterrupt:
            pass

def file_request_iter(path):
    yield pb.NestRequest(type=pb.CONFIG, config=pb.NestConfig(config=build_config_json()))
    with wave.open(path, 'rb') as wf:
        assert wf.getframerate() == SAMPLE_RATE and wf.getnchannels() == 1 and wf.getsampwidth() == 2
        while True:
            data = wf.readframes(FRAMES_PER_CHUNK)
            if not data:
                break
            yield pb.NestRequest(type=pb.DATA, data=pb.NestData(chunk=data))
            time.sleep(CHUNK_MS / 1000.0)

def parse_text(contents: str) -> str:
    try:
        obj = json.loads(contents)
        if isinstance(obj, dict):
            if 'result' in obj and isinstance(obj['result'], dict):
                return obj['result'].get('text') or obj['result'].get('msg') or contents
            return obj.get('text') or obj.get('msg') or obj.get('message') or contents
        return contents
    except Exception:
        return contents

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', '-f', help='Stream from WAV file (16k mono PCM)')
    args = ap.parse_args()
    if not API_KEY:
        print('Set CLOVASPEECH_API_KEY', file=sys.stderr)
        sys.exit(2)
    creds = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel(HOSTPORT, creds)
    stub = pbg.NestServiceStub(channel)
    meta = (('x-clovaspeech-api-key', API_KEY),)
    req_iter = file_request_iter(args.file) if args.file else mic_request_iter()
    try:
        for resp in stub.recognize(req_iter, metadata=meta):
            text = parse_text(resp.contents)
            if any(k in resp.contents for k in ['"isFinal":true', '"is_final":true']):
                print(f"\r{text}")
            else:
                print(f"\r… {text}", end='', flush=True)
    except grpc.RpcError as e:
        print('\n[gRPC error]', e.code().name, e.details(), file=sys.stderr)
        sys.exit(1)
    finally:
        print()

if __name__ == '__main__':
    main()





