import os
from PIL import Image, ImageOps
from Quartz import CGImageSourceCreateWithURL, CGImageSourceCreateImageAtIndex, CGImageSourceCreateWithData
from Foundation import NSURL, NSData



def create_cgimage_from_pil(pil_img):
    try:
        import io
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        
        ns_data = NSData.dataWithBytes_length_(img_data, len(img_data))
        
        image_source = CGImageSourceCreateWithData(ns_data, None)
        if image_source is None:
            return None
        
        cgimage = CGImageSourceCreateImageAtIndex(image_source, 0, None)
        return cgimage
    except Exception as e:
        return None
