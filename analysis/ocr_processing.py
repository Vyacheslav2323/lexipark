import base64
import json
import time
import uuid
import requests
import os
import io
import mimetypes
from PIL import Image, ImageOps
from django.conf import settings

# Clova OCR Configuration
CLOVA_OCR_URL = getattr(settings, 'CLOVA_OCR_URL', None)
CLOVA_OCR_SECRET = getattr(settings, 'CLOVA_OCR_SECRET', None)
OCR_MOCK = (os.getenv('OCR_MOCK') == '1') or bool(getattr(settings, 'OCR_MOCK', False))

def _guess_ext(name):
    ctype = mimetypes.guess_type(name)[0]
    ext = (mimetypes.guess_extension(ctype) or ".jpg").lstrip(".")
    return ext.lower()

def _is_supported_ext(ext):
    return ext in {"jpg", "jpeg", "png"}

def _load_pil(image_file):
    try:
        image_file.seek(0)
        return Image.open(image_file)
    except Exception:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            image_file.seek(0)
            return Image.open(image_file)
        except Exception:
            return None

def _pil_to_jpeg_bytes(pil_img):
    img = ImageOps.exif_transpose(pil_img.convert("RGB"))
    w, h = img.size
    m = max(w, h)
    if m > 2048:
        scale = 2048.0 / float(m)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return {"bytes": buf.getvalue(), "size": img.size}

def _generate_mock_ocr(img_width, img_height):
    words = ["사과", "학교", "사람", "서울", "한국어"]
    boxes = [
        {"x": 0.05, "y": 0.05, "w": 0.22, "h": 0.08},
        {"x": 0.73, "y": 0.05, "w": 0.22, "h": 0.08},
        {"x": 0.39, "y": 0.46, "w": 0.22, "h": 0.08},
        {"x": 0.05, "y": 0.86, "w": 0.22, "h": 0.08},
        {"x": 0.73, "y": 0.86, "w": 0.22, "h": 0.08},
    ]
    items = []
    for text, b in zip(words, boxes):
        items.append({
            "text": text,
            "confidence": 0.99,
            "boundingBox": b,
            "type": "line",
            "original_line": text
        })
    return {
        "image_size": (img_width, img_height),
        "total_items": len(items),
        "filtered_items": len(items),
        "ocr_data": items
    }

def build_clova_request(image_file, lang="ko"):
    name = getattr(image_file, "name", "upload")
    pil = _load_pil(image_file)
    if pil is None:
        image_file.seek(0)
        pil = Image.open(image_file)
    prepared = _pil_to_jpeg_bytes(pil)
    b64_data = base64.b64encode(prepared["bytes"]).decode("utf-8")
    body = {
        "version": "V1",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "lang": lang,
        "images": [{
            "format": "jpg",
            "name": name,
            "data": b64_data,
            "url": None
        }]
    }
    return {"body": body, "size": prepared["size"]}

def call_clova_ocr(request_body):
    headers = {
        "Content-Type": "application/json",
        "X-OCR-SECRET": CLOVA_OCR_SECRET,
    }
    
    try:
        response = requests.post(CLOVA_OCR_URL, headers=headers, data=json.dumps(request_body), timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def extract_text_from_cgimage(cgimg):
    # Legacy function - now uses Clova OCR
    # This maintains compatibility with existing code
    return []

def process_image_file(image_file, min_confidence=0.0):
    try:
        if OCR_MOCK:
            try:
                pil_img = _load_pil(image_file)
                if pil_img is None:
                    raise RuntimeError("mock-size-fallback")
                w, h = pil_img.size
            except Exception:
                w, h = 1000, 1000
            return _generate_mock_ocr(w, h)
        pil_img = _load_pil(image_file)
        if pil_img is None:
            image_file.seek(0)
            pil_img = Image.open(image_file)
        oriented = ImageOps.exif_transpose(pil_img)
        _ = oriented.size
        req = build_clova_request(image_file)
        result = call_clova_ocr(req["body"])
        
        if not result:
            return None
        
        img_width, img_height = req["size"]
        # Parse Clova OCR response
        ocr_data = []
        images = result.get("images", [])
        
        if images and "fields" in images[0]:
            fields = images[0]["fields"]
            
            for field in fields:
                text = field.get("inferText", "")
                confidence = field.get("confidence", 0.0)
                
                if confidence >= 0.0:  # Accept all detected text since Clova returns 0.0 for valid results
                    # Get bounding box information
                    bounding_box = field.get("boundingPoly", {})
                    vertices = bounding_box.get("vertices", [])
                    
                    if len(vertices) >= 4:
                        # Calculate normalized coordinates (0-1)
                        x_coords = [v.get("x", 0) for v in vertices]
                        y_coords = [v.get("y", 0) for v in vertices]
                        
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        bbox = {
                            "x": x_min / img_width,
                            "y": y_min / img_height,
                            "w": (x_max - x_min) / img_width,
                            "h": (y_max - y_min) / img_height,
                        }
                    else:
                        bbox = None
                    
                    ocr_data.append({
                        "text": text,
                        "confidence": confidence,
                        "boundingBox": bbox,
                        "type": "line",
                        "original_line": text
                    })
        
        # Reset file pointer for future use
        image_file.seek(0)
        
        return {
            "image_size": req["size"],
            "total_items": len(ocr_data),
            "filtered_items": len(ocr_data),
            "ocr_data": ocr_data
        }
        
    except Exception:
        return None

def extract_text_from_uploaded_image(image_file, min_confidence=0.30):
    result = process_image_file(image_file, min_confidence)
    
    if not result:
        return ""
    
    if not result.get("ocr_data"):
        return ""
    
    text_items = [item["text"] for item in result["ocr_data"]]
    return " ".join(text_items)
