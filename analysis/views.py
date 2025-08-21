from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from billing.decorators import subscription_required
import json
from .mecab_utils import analyze_sentence, translate_results, create_interactive_sentence, create_interactive_text_with_sentences, get_papago_translation
from vocab.models import Vocabulary
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from analysis.core.pipeline import analyze as pipeline_analyze, finish as pipeline_finish

def analyze_view(request):
    interactive_html = None
    analyzed_text = ''
    vocab_words = set()
    if request.method == 'POST':
        text = request.POST.get('textinput', '')
        if text.strip():
            analyzed_text = text
            res = pipeline_analyze({ 'user': request.user, 'text': text })
            interactive_html = res['html']
    context = {
        'interactive_html': interactive_html,
        'analyzed_text': analyzed_text
    }
    return render(request, 'analysis/page1.html', context)

@login_required
@csrf_exempt
def track_hover(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            korean_word = data.get('korean_word')
            duration = data.get('duration')
            
            if korean_word and duration is not None:
                vocab_entry = Vocabulary.objects.filter(
                    user=request.user,
                    korean_word=korean_word
                ).first()
                
                if vocab_entry:
                    vocab_entry.add_hover_duration(duration)
                    
                    return JsonResponse({
                        'success': True,
                        'hover_count': vocab_entry.hover_count,
                        'total_time': vocab_entry.total_hover_time,
                        'average_time': vocab_entry.get_average_duration(),
                        'last_5_durations': vocab_entry.get_durations()
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'message': 'Word not in vocabulary yet'
                    })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@csrf_exempt
def track_sentence_hover(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            punctuation = data.get('punctuation')
            duration = data.get('duration')
            
            if punctuation and duration is not None:
                return JsonResponse({
                    'success': True,
                    'message': f'Sentence hover tracked for punctuation: {punctuation}, duration: {duration}ms'
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

## deprecated finish endpoint removed; use /analysis/api/finish

## deprecated batch recall endpoint removed; use /analysis/api/batch-recall

## deprecated translate-sentence endpoint removed; use /analysis/api/translate-sentence

@login_required
@subscription_required
@csrf_exempt
def process_photo_ocr(request):
    if request.method == 'POST':
        try:
            
            if 'image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image file provided'})
            
            image_file = request.FILES['image']
            
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'File must be an image'})
            
            from .ocr_processing import extract_text_from_uploaded_image
            extracted_text = extract_text_from_uploaded_image(image_file)
            
            if extracted_text:
                return JsonResponse({
                    'success': True,
                    'text': extracted_text,
                    'message': 'Text extracted successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No text could be extracted from the image'
                })
                
        except Exception as e:
            print(f"Error in process_photo_ocr: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

## deprecated analyze-ocr-text endpoint removed; use /analysis/api/analyze

@login_required
@subscription_required
def image_analysis_view(request):
    if request.method == 'POST':
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image file provided'})
            
            image_file = request.FILES['image']
            confidence = float(request.POST.get('confidence', 0.30))
            
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'File must be an image'})
            
            from .ocr_processing import process_image_file
            result = process_image_file(image_file, confidence)
            
            if result:
                return JsonResponse({
                    'success': True,
                    'ocr_data': result
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'OCR processing failed'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - render the template
    vocab_words = set()
    if request.user.is_authenticated:
        vocab_words = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
    
    import json as _json
    context = {
        'vocab_words_json': _json.dumps(list(vocab_words))
    }
    return render(request, 'analysis/image_analysis.html', context)


## deprecated per-sentence analyze endpoint removed; use /analysis/api/analyze


@csrf_exempt
def translate_word(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word = data.get('word', '')
            if not word:
                return JsonResponse({'success': False, 'error': 'No word provided'})
            if request.user.is_authenticated:
                vocab = Vocabulary.objects.filter(user=request.user, korean_word=word).first()
                if vocab and vocab.english_translation:
                    return JsonResponse({'success': True, 'translation': vocab.english_translation})
            try:
                from vocab.models import GlobalTranslation
                gt = GlobalTranslation.objects.filter(korean_word=word).first()
                if gt and gt.english_translation:
                    gt.usage_count += 1
                    gt.save()
                    return JsonResponse({'success': True, 'translation': gt.english_translation})
            except Exception:
                pass
            translation = get_papago_translation(word)
            return JsonResponse({'success': True, 'translation': translation})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

## deprecated api/v1 analyzes removed; use unified /analysis/api/*

## deprecated api/v1 analyzes removed; use unified /analysis/api/*
