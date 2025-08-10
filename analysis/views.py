from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .mecab_utils import analyze_sentence, translate_results, create_interactive_sentence, create_interactive_text_with_sentences
from vocab.models import Vocabulary

def analyze_view(request):
    results = None
    translations = None
    interactive_html = None
    vocab_words = set()
    
    if request.method == 'POST':
        text = request.POST.get('textinput', '')
        if text.strip():
            results = analyze_sentence(text)
            translations = translate_results(results)
            
            if request.user.is_authenticated:
                vocab_words = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
            else:
                vocab_words = set()
            
            interactive_html = create_interactive_text_with_sentences(text, vocab_words)
    
    context = {
        'results': results,
        'translations': translations,
        'interactive_html': interactive_html,
        'analyzed_text': text if 'text' in locals() else ''
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

@login_required
@csrf_exempt
def finish_analysis_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if text.strip():
                results = analyze_sentence(text)
                translations = translate_results(results)
                words = [r[1] for r in results if r[1] is not None and any('\uAC00' <= char <= '\uD7A3' for char in str(r[1]))]
                user_vocab = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
                new_words = [w for w in words if w not in user_vocab]
                
                word_data = {}
                for i, (surface, base, pos, grammar_info) in enumerate(results):
                    if base is not None and any('\uAC00' <= char <= '\uD7A3' for char in str(base)):
                        word_data[base] = {
                            'pos': pos,
                            'grammar_info': grammar_info,
                            'translation': translations[i] if i < len(translations) else base
                        }
                
                for w in new_words:
                    data = word_data.get(w, {'pos': '', 'grammar_info': '', 'translation': w})
                    vocab_entry, created = Vocabulary.objects.get_or_create(
                        user=request.user,
                        korean_word=w,
                        defaults={
                            'pos': data['pos'],
                            'grammar_info': data['grammar_info'],
                            'english_translation': data['translation'],
                            'hover_count': 0,
                            'total_hover_time': 0.0,
                            'last_5_durations': '[]',
                            'retention_rate': 1.0,
                            'alpha_prior': 10,
                            'beta_prior': 0
                        }
                    )
                    if not created:
                        vocab_entry.alpha_prior = 10
                        vocab_entry.beta_prior = 0
                        vocab_entry.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Added {len(new_words)} words to vocabulary',
                    'words_added': new_words
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@csrf_exempt
def batch_update_recalls_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            interactions = data.get('interactions', [])
            
            updated_count = 0
            for korean_word, had_lookup in interactions:
                vocab_entry = Vocabulary.objects.filter(
                    user=request.user,
                    korean_word=korean_word
                ).first()
                
                if vocab_entry:
                    from vocab.bayesian_recall import update_vocabulary_recall
                    vocab_entry = update_vocabulary_recall(vocab_entry, had_lookup)
                    vocab_entry.save()
                    updated_count += 1
            
            return JsonResponse({
                'success': True,
                'updated_count': updated_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def translate_sentence(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sentence = data.get('sentence', '')
            
            if sentence.strip():
                from .mecab_utils import get_sentence_translation
                translation = get_sentence_translation(sentence)
                return JsonResponse({'translation': translation})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
@csrf_exempt
def process_photo_ocr(request):
    if request.method == 'POST':
        try:
            print(f"Processing photo OCR request from user: {request.user}")
            print(f"Files received: {list(request.FILES.keys())}")
            
            if 'image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image file provided'})
            
            image_file = request.FILES['image']
            print(f"Image file: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")
            
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'File must be an image'})
            
            from .ocr_processing import extract_text_from_uploaded_image
            print("Starting OCR processing...")
            extracted_text = extract_text_from_uploaded_image(image_file)
            print(f"OCR result: {extracted_text[:100] if extracted_text else 'None'}")
            
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

def image_analysis_view(request):
    from django.shortcuts import redirect
    return redirect('analysis:analyze')


