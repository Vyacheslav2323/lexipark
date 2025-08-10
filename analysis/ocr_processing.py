import base64
import json
import time
import uuid
import requests
import os
import mimetypes
from PIL import Image, ImageOps
from django.conf import settings

# Clova OCR Configuration
CLOVA_OCR_URL = getattr(settings, 'CLOVA_OCR_URL', 'https://sc3y9jhv73.apigw.ntruss.com/custom/v1/45060/e7f1a66c25fa7771cced95aba1bb01b4c64bc1c18bd36dfc5abbc516412521fa/general')
CLOVA_OCR_SECRET = getattr(settings, 'CLOVA_OCR_SECRET', 'ZWFWSlJwaG5ZVGFZcWJDbnFUVGRKbWdiQVh5eHdhYlU=')

def build_clova_request(image_file, lang="ko"):
    ext = (mimetypes.guess_extension(mimetypes.guess_type(image_file.name)[0]) or ".jpg").lstrip(".")
    
    # Read and encode image
    image_data = image_file.read()
    b64_data = base64.b64encode(image_data).decode("utf-8")
    
    return {
        "version": "V1",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "lang": lang,
        "images": [{
            "format": ext,
            "name": image_file.name,
            "data": b64_data,
            "url": None
        }]
    }

def call_clova_ocr(request_body):
    headers = {
        "Content-Type": "application/json",
        "X-OCR-SECRET": CLOVA_OCR_SECRET,
    }
    
    try:
        response = requests.post(CLOVA_OCR_URL, headers=headers, data=json.dumps(request_body), timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Clova OCR API call failed: {e}")
        return None

def extract_text_from_cgimage(cgimg):
    # Legacy function - now uses Clova OCR
    # This maintains compatibility with existing code
    return []

def process_image_file(image_file, min_confidence=0.0):  # Clova OCR returns 0.0 for valid text
    try:
        # Reset file pointer
        image_file.seek(0)
        
        # Get image dimensions first
        pil_img = Image.open(image_file)
        img_width, img_height = pil_img.size
        
        # Build Clova OCR request
        request_body = build_clova_request(image_file)
        
        # Call Clova OCR
        result = call_clova_ocr(request_body)
        
        if not result:
            print(f"Clova OCR returned no result")
            return None
        
        print(f"Clova OCR response: {result}")
        
        # Parse Clova OCR response
        ocr_data = []
        images = result.get("images", [])
        
        print(f"Images in response: {images}")
        
        if images and "fields" in images[0]:
            fields = images[0]["fields"]
            print(f"Found {len(fields)} fields in image")
            
            for field in fields:
                text = field.get("inferText", "")
                confidence = field.get("confidence", 0.0)
                print(f"Field: text='{text}', confidence={confidence}")
                
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
            "image_size": (pil_img.width, pil_img.height),
            "total_items": len(ocr_data),
            "filtered_items": len(ocr_data),
            "ocr_data": ocr_data
        }
        
    except Exception as e:
        print(f"Error in process_image_file: {e}")
        return None

def extract_text_from_uploaded_image(image_file, min_confidence=0.30):
    result = process_image_file(image_file, min_confidence)
    
    if not result:
        return ""
    
    if not result.get("ocr_data"):
        return ""
    
    text_items = [item["text"] for item in result["ocr_data"]]
    return " ".join(text_items)
