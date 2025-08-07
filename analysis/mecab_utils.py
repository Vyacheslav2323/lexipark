# -*- coding: utf-8 -*-
import requests
import json
import re
import os

# Import MeCab for Korean text analysis
from MeCab import Tagger

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
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result["message"]["result"]["translatedText"]
            return translated_text
        else:
            print(f"DEBUG: Papago API error - Status: {response.status_code}")
            print(f"DEBUG: Papago API error - Response: {response.text[:200]}")
            return text
    except Exception as e:
        print(f"DEBUG: Papago API exception: {e}")
        return text

def tokenize(text):
    tagger = Tagger()
    parsed = tagger.parse(text)
    if parsed is None:
        return []
    tokens = []
    for line in parsed.split('\n'):
        if line == 'EOS' or not line.strip():
            continue
        surface = line.split('\t')[0]
        tokens.append(surface)
    return tokens

def analyze_token(surface, pos, features):
    if pos in ['NNG', 'NNP', 'NP', 'NR', 'MAG', 'MAJ', 'MM']:
        return surface
    if 'VV' in pos or 'VA' in pos or 'VX' in pos:
        if 'Inflect' in features:
            inflect_info = features[-1].split('+')[0]
            base = inflect_info.split('/')[0]
            if base.endswith('다'):
                return base
            return base + '다'
        base = features[3] if len(features) > 3 and features[3] != '*' else surface
        if base.endswith('다'):
            return base
        return base + '다'
    if pos in ['SF', 'SE', 'SSO', 'SSC', 'SC', 'SY', 'SL', 'SH', 'SN', 'UNA', 'NA', 'VSV']:
        return None
    return pos

def analyze_sentence(sentence):
    try:
        tagger = Tagger()
        parsed = tagger.parse(sentence)
        print(f"PRODUCTION DEBUG: MeCab parsed result: {parsed}")
        
        if parsed is None:
            print("PRODUCTION DEBUG: MeCab returned None")
            return []
            
        results = []
        for line in parsed.split('\n'):
            if line == 'EOS' or not line.strip():
                continue
            surface, features_str = line.split('\t')
            features = features_str.split(',')
            pos = features[0]
            result = analyze_token(surface, pos, features)
            grammar_info = ','.join(features[1:]) if len(features) > 1 else ''
            results.append((surface, result, pos, grammar_info))
        
        print(f"PRODUCTION DEBUG: MeCab analysis results: {results}")
        return results
    except Exception as e:
        print(f"PRODUCTION DEBUG: MeCab error: {e}")
        return []

def translate_results(results):
    translations = []
    for surface, result, pos, grammar_info in results:
        if result is None:
            translations.append(None)
            continue
        if isinstance(result, str) and result not in ['NNG', 'NNP', 'NP', 'NR', 'MAG', 'MAJ', 'MM']:
            if any('\u3131' <= char <= '\u318E' or '\uAC00' <= char <= '\uD7A3' for char in result):
                translation = get_papago_translation(result)
                translations.append(translation)
            else:
                translations.append(result)
            continue
        if isinstance(result, str) and any('\u3131' <= char <= '\u318E' or '\uAC00' <= char <= '\uD7A3' for char in result):
            translation = get_papago_translation(result)
            translations.append(translation)
        else:
            translations.append(result)
    return translations

def retention_to_color(retention_rate):
    if retention_rate >= 1.0:
        return "transparent"
    alpha = 1 - (retention_rate - 0.1) / 0.9
    alpha = max(0, min(1, alpha))
    return f"rgba(255, 255, 0, {alpha:.2f})"

def create_interactive_sentence(sentence, results, translations, vocab_words=None):
    if vocab_words is None:
        vocab_words = set()
    
    html_parts = []
    current_pos = 0
    
    for i, ((surface, base, pos, grammar_info), translation) in enumerate(zip(results, translations)):
        if base is None:
            continue
            
        start_pos = sentence.find(surface, current_pos)
        if start_pos == -1:
            continue
            
        if start_pos > current_pos:
            html_parts.append(f'<span>{sentence[current_pos:start_pos]}</span>')
        
        # Check if the surface text contains Korean characters, regardless of POS tags
        is_korean = any('\uAC00' <= char <= '\uD7A3' for char in str(surface))
        
        if is_korean:
            css_class = 'interactive-word'
            if base in vocab_words:
                try:
                    from vocab.models import Vocabulary
                    vocab_entry = Vocabulary.objects.filter(korean_word=base).first()
                    if vocab_entry:
                        color = retention_to_color(vocab_entry.get_retention_rate())
                        html_parts.append(f'<span class="{css_class}" data-translation="{translation}" data-original="{base}" data-pos="{pos}" data-grammar="{grammar_info}" style="background-color: {color}">{sentence[start_pos:start_pos + len(surface)]}</span>')
                    else:
                        html_parts.append(f'<span class="{css_class}" data-translation="{translation}" data-original="{base}" data-pos="{pos}" data-grammar="{grammar_info}">{sentence[start_pos:start_pos + len(surface)]}</span>')
                except:
                    html_parts.append(f'<span class="{css_class}" data-translation="{translation}" data-original="{base}" data-pos="{pos}" data-grammar="{grammar_info}">{sentence[start_pos:start_pos + len(surface)]}</span>')
            else:
                html_parts.append(f'<span class="{css_class}" data-translation="{translation}" data-original="{base}" data-pos="{pos}" data-grammar="{grammar_info}">{sentence[start_pos:start_pos + len(surface)]}</span>')
        else:
            html_parts.append(f'<span>{sentence[start_pos:start_pos + len(surface)]}</span>')
        
        current_pos = start_pos + len(surface)
    
    if current_pos < len(sentence):
        html_parts.append(f'<span>{sentence[current_pos:]}</span>')
    
    return ''.join(html_parts)

def split_text_into_sentences(text):
    import re
    
    sentence_endings = r'[.!?](?=\s|$|[가-힣])'
    sentences = re.split(f'({sentence_endings})', text)
    result = []
    
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            sentence = sentences[i].strip()
            punctuation = sentences[i + 1]
            if sentence:
                result.append((sentence, punctuation))
        else:
            sentence = sentences[i].strip()
            if sentence:
                result.append((sentence, ''))
    
    return result

def get_sentence_translation(sentence):
    try:
        from vocab.models import GlobalTranslation
        
        cached_translation = GlobalTranslation.objects.filter(korean_word=sentence).first()
        if cached_translation:
            cached_translation.usage_count += 1
            cached_translation.save()
            return cached_translation.english_translation
        
        translation = _request_papago_api(sentence)
        if translation != sentence:
            try:
                GlobalTranslation.objects.get_or_create(
                    korean_word=sentence,
                    defaults={'english_translation': translation}
                )
            except Exception as db_error:
                print(f"Translation error for sentence '{sentence}': {db_error}")
        return translation
    except Exception as e:
        print(f"Translation error for sentence '{sentence}': {e}")
        return sentence

def create_interactive_text_with_sentences(text, vocab_words=None):
    if vocab_words is None:
        vocab_words = set()
    
    # Process the entire text as one sentence for word-level analysis
    results = analyze_sentence(text)
    translations = translate_results(results)
    interactive_html = create_interactive_sentence(text, results, translations, vocab_words)
    
    return interactive_html

def get_papago_translation(word):
    try:
        from vocab.models import GlobalTranslation
        
        cached_translation = GlobalTranslation.objects.filter(korean_word=word).first()
        if cached_translation:
            cached_translation.usage_count += 1
            cached_translation.save()
            return cached_translation.english_translation
        
        translation = _request_papago_api(word)
        if translation != word:
            try:
                GlobalTranslation.objects.get_or_create(
                    korean_word=word,
                    defaults={'english_translation': translation}
                )
            except Exception as db_error:
                print(f"Translation error for '{word}': {db_error}")
        return translation
    except Exception as e:
        print(f"Translation error for '{word}': {e}")
        return word


