from Vision import VNRecognizeTextRequest, VNImageRequestHandler, VNRequestTextRecognitionLevelAccurate
from .image_handling import create_cgimage_from_pil
from PIL import Image, ImageOps
import os

def setup_vision_request():
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    request.setRecognitionLanguages_(['ko-KR', 'en-US'])
    return request

def extract_text_from_cgimage(cgimg):
    try:
        request = setup_vision_request()
        handler = VNImageRequestHandler.alloc().initWithCGImage_options_(cgimg, None)
        
        success, error = handler.performRequests_error_([request], None)
        if not success:
            return []
        
        observations = request.results() or []
        if not observations:
            return []
        
        extracted = []
        
        for observation in observations:
            candidates = observation.topCandidates_(1)
            
            if candidates:
                text = str(candidates[0].string()).strip()
                confidence = float(candidates[0].confidence())
                
                bbox = observation.boundingBox()
                if bbox:
                    extracted.append({
                        "text": text,
                        "confidence": confidence,
                        "boundingBox": {
                            "x": float(bbox.origin.x),
                            "y": 1.0 - float(bbox.origin.y) - float(bbox.size.height),
                            "w": float(bbox.size.width),
                            "h": float(bbox.size.height),
                        },
                        "type": "line",
                        "original_line": text
                    })
                else:
                    extracted.append({
                        "text": text,
                        "confidence": confidence,
                        "boundingBox": None,
                        "type": "line",
                        "original_line": text
                    })
        
        return extracted
    except Exception as e:
        return []



def process_image_file(image_file, min_confidence=0.30):
    try:
        from .image_handling import create_cgimage_from_pil
        
        pil_img = Image.open(image_file)
        pil_img = ImageOps.exif_transpose(pil_img)
        pil_img = pil_img.convert("RGB")
        
        cgimg = create_cgimage_from_pil(pil_img)
        if not cgimg:
            return None
        
        raw_results = extract_text_from_cgimage(cgimg)
        filtered_raw = [r for r in raw_results if r["confidence"] >= min_confidence]
        
        return {
            "image_size": pil_img.size,
            "total_items": len(raw_results),
            "filtered_items": len(filtered_raw),
            "ocr_data": filtered_raw
        }
        
    except Exception as e:
        return None

def extract_text_from_uploaded_image(image_file, min_confidence=0.30):
    result = process_image_file(image_file, min_confidence)
    
    if not result:
        return ""
    
    if not result.get("ocr_data"):
        return ""
    
    text_items = [item["text"] for item in result["ocr_data"]]
    return " ".join(text_items)
