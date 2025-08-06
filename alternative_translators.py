import requests
import json
import os
from typing import Optional

def get_naver_papago_translation(text: str) -> str:
    try:
        # Import Django models only when needed
        from django.apps import apps
        if apps.is_installed('vocab'):
            from vocab.models import GlobalTranslation
            
            cached_translation = GlobalTranslation.objects.filter(korean_word=text).first()
            if cached_translation:
                cached_translation.usage_count += 1
                cached_translation.save()
                return cached_translation.english_translation
                
            translation = _request_papago_api(text)
            if translation != text:
                GlobalTranslation.objects.create(
                    korean_word=text,
                    english_translation=translation
                )
            return translation
        else:
            # Fallback if vocab app is not available
            return _request_papago_api(text)
    except Exception as e:
        print(f"Papago translation error for '{text}': {e}")
        return text

def _request_papago_api(text: str) -> str:
    url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "x-ncp-apigw-api-key-id": os.getenv('NAVER_CLIENT_ID', 'x8wqn9022w'),
        "x-ncp-apigw-api-key": os.getenv('NAVER_CLIENT_SECRET', 'c8BMfUF2lqFldkpcFe6k2j5GKGvleIPkpPvHraSC'),
        "Content-Type": "application/json"
    }
    data = {
        "source": "ko",
        "target": "en",
        "text": text
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        return result["message"]["result"]["translatedText"]
    return text

def translate_with_alternative(text: str, service: str = "papago") -> str:
    if service == "papago":
        return get_naver_papago_translation(text)
    else:
        print(f"Unknown service: {service}")
        return text 