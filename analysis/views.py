from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .mecab_utils import analyze_sentence, translate_results, create_interactive_sentence, create_interactive_text_with_sentences
from vocab.models import Vocabulary
from vocab.bayesian_recall import update_vocabulary_recall

# Create your views here.

def health_check(request):
    try:
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("OK", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"Database Error: {str(e)}", content_type="text/plain", status=500)

def analyze_view(request):
    results = None
    translations = None
    interactive_html = None
    vocab_words = set()
    
    try:
        if request.method == 'POST':
            if request.POST.get('know_rest') == '1':
                text = request.POST.get('textinput', '')
                
                results = analyze_sentence(text)
                translations = translate_results(results)
                words = [r[0] for r in results if r[0] is not None and any('\uAC00' <= char <= '\uD7A3' for char in str(r[0]))]
                
                user_vocab = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
                new_words = [w for w in words if w not in user_vocab]
                existing_vocab_words = [w for w in words if w in user_vocab]
                
                word_data = {}
                for i, (surface, base, pos, grammar_info) in enumerate(results):
                    if surface is not None and any('\uAC00' <= char <= '\uD7A3' for char in str(surface)):
                        word_data[surface] = {
                            'pos': pos,
                            'grammar_info': grammar_info,
                            'translation': translations[i] if i < len(translations) else surface
                        }
                
                for w in new_words:
                    data = word_data.get(w, {'pos': '', 'grammar_info': '', 'translation': w})
                    Vocabulary.objects.get_or_create(
                        user=request.user,
                        korean_word=w,
                        defaults={
                            'pos': data['pos'],
                            'grammar_info': data['grammar_info'],
                            'english_translation': data['translation'],
                            'hover_count': 0,
                            'total_hover_time': 0.0,
                            'last_5_durations': '[]',
                            'retention_rate': 0.91,
                            'recall_failures': 0.0,
                            'recall_successes': 0.0,
                            'alpha_prior': 10.0,
                            'beta_prior': 0.0
                        }
                    )
                
                if request.user.is_authenticated and existing_vocab_words:
                    from vocab.bayesian_recall import batch_update_recalls
                    success_interactions = [(word, False) for word in existing_vocab_words]
                    batch_update_recalls(request.user, success_interactions)
                
                vocab_words = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
                interactive_html = create_interactive_text_with_sentences(text, vocab_words)
            else:
                text = request.POST.get('textinput', '')
                if text.strip():
                    if request.user.is_authenticated:
                        vocab_words = set(Vocabulary.objects.filter(user=request.user).values_list('korean_word', flat=True))
                    
                    interactive_html = create_interactive_text_with_sentences(text, vocab_words)
        
        context = {
            'results': results,
            'translations': translations,
            'interactive_html': interactive_html
        }
        return render(request, 'analysis/page1.html', context)
    except Exception as e:
        print(f"Error in analyze_view: {e}")
        import traceback
        traceback.print_exc()
        context = {
            'results': None,
            'translations': None,
            'interactive_html': f'<p class="text-danger">Error: {str(e)}</p>'
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
                    
                    had_lookup = duration > 1000
                    vocab_entry = update_vocabulary_recall(vocab_entry, had_lookup)
                    vocab_entry.save()
                    
                    return JsonResponse({
                        'success': True,
                        'hover_count': vocab_entry.hover_count,
                        'total_time': vocab_entry.total_hover_time,
                        'average_time': vocab_entry.get_average_duration(),
                        'last_5_durations': vocab_entry.get_durations(),
                        'retention_rate': vocab_entry.retention_rate
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
def batch_update_recalls_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_interactions = data.get('interactions', [])
            
            if word_interactions:
                from vocab.bayesian_recall import batch_update_recalls
                updated_count = batch_update_recalls(request.user, word_interactions)
                
                return JsonResponse({
                    'success': True,
                    'updated_count': updated_count
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No interactions provided'
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
