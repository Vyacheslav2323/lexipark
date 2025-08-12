from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .mecab_utils import analyze_sentence, translate_results, create_interactive_sentence, create_interactive_text_with_sentences, get_papago_translation
from vocab.models import Vocabulary

def analyze_view(request):
    interactive_html = None
    analyzed_text = ''
    vocab_words = set()
    if request.method == 'POST':
        text = request.POST.get('textinput', '')
        if text.strip():
            analyzed_text = text
            if request.user.is_authenticated:
                vocab_words = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
            interactive_html = create_interactive_text_with_sentences(text, vocab_words)
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

@login_required
@csrf_exempt
def analyze_ocr_text(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if not text.strip():
                return JsonResponse({'success': False, 'error': 'No text provided'})
            
            results = analyze_sentence(text)
            
            user_vocab_qs = Vocabulary.objects.filter(user=request.user)
            vocab_words = set(user_vocab_qs.values_list('korean_word', flat=True))
            vocab_map = {v.korean_word: v.english_translation for v in user_vocab_qs}
            try:
                from vocab.models import GlobalTranslation
                bases = [b for (_, b, _, _) in results if b]
                globals_qs = GlobalTranslation.objects.filter(korean_word__in=bases)
                global_map = {g.korean_word: g.english_translation for g in globals_qs}
            except Exception:
                global_map = {}
            
            # Process each word with vocabulary info
            words_data = []
            for (surface, base, pos, grammar_info) in results:
                if base is None:
                    continue
                    
                word_info = {
                    'surface': surface,
                    'base': base,
                    'pos': pos,
                    'grammar_info': grammar_info,
                    'translation': global_map.get(base) or vocab_map.get(base),
                    'in_vocab': base in vocab_words
                }
                
                # Add color if in vocabulary
                if word_info['in_vocab']:
                    try:
                        vocab_entry = Vocabulary.objects.filter(korean_word=base).first()
                        if vocab_entry:
                            from .mecab_utils import retention_to_color
                            word_info['color'] = retention_to_color(vocab_entry.get_retention_rate())
                    except:
                        pass
                
                words_data.append(word_info)
            
            return JsonResponse({
                'success': True,
                'words': words_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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


@csrf_exempt
def analyze_sentence_chunk(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sentence = data.get('sentence', '')
            if not sentence.strip():
                return JsonResponse({'success': False, 'error': 'Empty sentence'})
            vocab_words = set()
            vocab_map = {}
            if request.user.is_authenticated:
                qs = Vocabulary.objects.filter(user=request.user)
                vocab_words = set(qs.values_list('korean_word', flat=True))
                vocab_map = {v.korean_word: v.english_translation for v in qs}
            results = analyze_sentence(sentence)
            translations = []
            for _, base, _, _ in results:
                if base is None:
                    translations.append(None)
                else:
                    translations.append(vocab_map.get(base, ''))
            html = create_interactive_sentence(sentence, results, translations, vocab_words)
            return JsonResponse({'success': True, 'html': html})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


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
