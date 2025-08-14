from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from billing.decorators import subscription_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Vocabulary, GlobalTranslation
from analysis.mecab_utils import analyze_sentence
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

@login_required
@subscription_required
def vocabulary_test(request):
    return render(request, 'vocab/vocabulary_test.html')

@login_required
@subscription_required
def get_test_ranks(request):
    try:
        limit = int(request.GET.get('limit', '5000'))
    except Exception:
        limit = 5000
    qs = GlobalTranslation.objects.order_by('-usage_count').values_list('korean_word', flat=True)[:limit]
    words = [{'rank': idx + 1, 'word': w} for idx, w in enumerate(qs)]
    return JsonResponse({'success': True, 'words': words})

@login_required
@subscription_required
@require_POST
@csrf_exempt
def update_alpha_prior(request):
    word = request.POST.get('word')
    alpha_value = request.POST.get('alpha')
    if not word or alpha_value is None:
        return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)
    try:
        alpha_float = float(alpha_value)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid alpha'}, status=400)
    with transaction.atomic():
        vocab, _ = Vocabulary.objects.get_or_create(
            user=request.user,
            korean_word=word,
            defaults=_defaults_for_word(word)
        )
        vocab.alpha_prior = alpha_float
        vocab.save(update_fields=['alpha_prior', 'last_reviewed'])
    return JsonResponse({'success': True, 'alpha': alpha_float})

def _defaults_for_word(word):
    pos = ''
    grammar_info = ''
    try:
        res = analyze_sentence(word)
        if res:
            _, _, pos, grammar_info = res[0]
    except Exception:
        pos = ''
    translation = word
    try:
        gt = GlobalTranslation.objects.filter(korean_word=word).first()
        if gt:
            translation = gt.english_translation
    except Exception:
        translation = word
    return {'pos': pos, 'grammar_info': grammar_info, 'english_translation': translation}

@login_required
@subscription_required
@require_POST
@csrf_exempt
def batch_update_adaptive(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    alpha_updates = data.get('alpha', [])
    beta_updates = data.get('beta', [])
    if not isinstance(alpha_updates, list) or not isinstance(beta_updates, list):
        return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)
    # consolidate deltas per word
    alpha_map = {}
    for w, d in alpha_updates:
        try:
            alpha_map[w] = alpha_map.get(w, 0.0) + float(d)
        except Exception:
            continue
    beta_map = {}
    for w, d in beta_updates:
        try:
            beta_map[w] = beta_map.get(w, 0.0) + float(d)
        except Exception:
            continue
    all_words = list(set(list(alpha_map.keys()) + list(beta_map.keys())))
    updated = {'alpha': 0, 'beta': 0}
    now = timezone.now()
    with transaction.atomic():
        if not all_words:
            return JsonResponse({'success': True, 'updated': updated})
        existing = {
            v.korean_word: v for v in 
            Vocabulary.objects.filter(user=request.user, korean_word__in=all_words)
        }
        missing_words = [w for w in all_words if w not in existing]
        if missing_words:
            gt_map = {
                g.korean_word: g.english_translation
                for g in GlobalTranslation.objects.filter(korean_word__in=missing_words)
            }
            to_create = [
                Vocabulary(
                    user=request.user,
                    korean_word=w,
                    pos='',
                    grammar_info='',
                    english_translation=gt_map.get(w, w)
                )
                for w in missing_words
            ]
            Vocabulary.objects.bulk_create(to_create, ignore_conflicts=True)
            for v in Vocabulary.objects.filter(user=request.user, korean_word__in=missing_words):
                existing[v.korean_word] = v
        to_update = []
        for w, v in existing.items():
            a = alpha_map.get(w, 0.0)
            b = beta_map.get(w, 0.0)
            if a == 0.0 and b == 0.0:
                continue
            if a:
                v.alpha_prior = float(v.alpha_prior) + a
                updated['alpha'] += 1
            if b:
                v.beta_prior = float(v.beta_prior) + b
                updated['beta'] += 1
            v.last_reviewed = now
            to_update.append(v)
        chunk = 500
        for i in range(0, len(to_update), chunk):
            Vocabulary.objects.bulk_update(
                to_update[i:i+chunk], ['alpha_prior', 'beta_prior', 'last_reviewed']
            )
    return JsonResponse({'success': True, 'updated': updated})

@api_view(['GET'])
@permission_classes([AllowAny])
def api_get_ranks(request):
    try:
        limit = int(request.GET.get('limit', '5000'))
    except Exception:
        limit = 5000
    qs = GlobalTranslation.objects.order_by('-usage_count').values_list('korean_word', flat=True)[:limit]
    words = [{'rank': idx + 1, 'word': w} for idx, w in enumerate(qs)]
    return JsonResponse({'success': True, 'words': words})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_batch_update(request):
    try:
        data = request.data
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    alpha_updates = data.get('alpha', [])
    beta_updates = data.get('beta', [])
    if not isinstance(alpha_updates, list) or not isinstance(beta_updates, list):
        return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)
    alpha_map = {}
    for w, d in alpha_updates:
        try:
            alpha_map[w] = alpha_map.get(w, 0.0) + float(d)
        except Exception:
            continue
    beta_map = {}
    for w, d in beta_updates:
        try:
            beta_map[w] = beta_map.get(w, 0.0) + float(d)
        except Exception:
            continue
    all_words = list(set(list(alpha_map.keys()) + list(beta_map.keys())))
    updated = {'alpha': 0, 'beta': 0}
    now = timezone.now()
    with transaction.atomic():
        if not all_words:
            return JsonResponse({'success': True, 'updated': updated})
        existing = {v.korean_word: v for v in Vocabulary.objects.filter(user=request.user, korean_word__in=all_words)}
        missing_words = [w for w in all_words if w not in existing]
        if missing_words:
            gt_map = {g.korean_word: g.english_translation for g in GlobalTranslation.objects.filter(korean_word__in=missing_words)}
            to_create = [
                Vocabulary(
                    user=request.user,
                    korean_word=w,
                    pos='',
                    grammar_info='',
                    english_translation=gt_map.get(w, w)
                ) for w in missing_words
            ]
            Vocabulary.objects.bulk_create(to_create, ignore_conflicts=True)
            for v in Vocabulary.objects.filter(user=request.user, korean_word__in=missing_words):
                existing[v.korean_word] = v
        to_update = []
        for w, v in existing.items():
            a = alpha_map.get(w, 0.0)
            b = beta_map.get(w, 0.0)
            if a == 0.0 and b == 0.0:
                continue
            if a:
                v.alpha_prior = float(v.alpha_prior) + a
                updated['alpha'] += 1
            if b:
                v.beta_prior = float(v.beta_prior) + b
                updated['beta'] += 1
            v.last_reviewed = now
            to_update.append(v)
        chunk = 500
        for i in range(0, len(to_update), chunk):
            Vocabulary.objects.bulk_update(to_update[i:i+chunk], ['alpha_prior', 'beta_prior', 'last_reviewed'])
    return JsonResponse({'success': True, 'updated': updated})
