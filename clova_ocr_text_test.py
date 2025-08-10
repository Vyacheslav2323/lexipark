# clova_ocr_text_test.py
import base64, json, time, uuid, requests, os, mimetypes

APIGW_INVOKE_URL = "https://sc3y9jhv73.apigw.ntruss.com/custom/v1/45060/e7f1a66c25fa7771cced95aba1bb01b4c64bc1c18bd36dfc5abbc516412521fa/general"
X_OCR_SECRET     = "ZWFWSlJwaG5ZVGFZcWJDbnFUVGRKbWdiQVh5eHdhYlU="
IMAGE_PATH       = "/Users/slimslavik/Downloads/test.jpg"   # use a real image path
LANG             = "ko"           # or "ko,en" if mixed

def body_from_file(path, lang="ko"):
    fmt = (mimetypes.guess_extension(mimetypes.guess_type(path)[0]) or ".jpg").lstrip(".")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return {
        "version": "V1",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "lang": lang,
        "images": [{
            "format": fmt, "name": os.path.basename(path),
            "data": b64, "url": None
        }]
    }

def body_from_url(url, lang="ko", fmt="jpg", name="remote"):
    return {
        "version": "V1",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "lang": lang,
        "images": [{
            "format": fmt, "name": name,
            "data": None, "url": url
        }]
    }

def call_ocr(body):
    headers = {"Content-Type": "application/json", "X-OCR-SECRET": X_OCR_SECRET}
    r = requests.post(APIGW_INVOKE_URL, headers=headers, data=json.dumps(body), timeout=20)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # Option A: local file
    body = body_from_file(IMAGE_PATH, lang=LANG)

    # Option B: public URL (uncomment to try)
    # body = body_from_url("https://kr.object.ncloudstorage.com/ocr-img/OCR_ko(1)REAN_ko(1).png",
    #                      lang=LANG, fmt="png", name="demo")

    res = call_ocr(body)
    print(json.dumps(res, ensure_ascii=False, indent=2))

    print("\n=== Extracted Text ===")
    images = res.get("images", [])
    if images and "fields" in images[0]:
        for f in images[0]["fields"]:
            print(f.get("inferText", ""))
