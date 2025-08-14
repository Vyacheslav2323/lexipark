from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from billing.decorators import subscription_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from vocab.models import Vocabulary
from vocab.bayesian_recall import update_vocabulary_recall
from .forms import CustomUserCreationForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from billing.models import Subscription

# Create your views here.

def privacy_view(request):
    return render(request, 'users/privacy.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
@subscription_required
def profile_view(request):
    vocabularies = Vocabulary.objects.filter(user=request.user)
    context = {
        'vocabularies': vocabularies,
        'total_words': vocabularies.count()
    }
    return render(request, 'users/profile.html', context)

@login_required
def stats_view(request):
    end = timezone.now().date()
    start = end - timedelta(days=6)
    days = [start + timedelta(days=i) for i in range(7)]
    vocab = Vocabulary.objects.filter(user=request.user, created_at__date__gte=start, created_at__date__lte=end)
    reviewed = Vocabulary.objects.filter(user=request.user, last_reviewed__date__gte=start, last_reviewed__date__lte=end)
    added_map = {d: 0 for d in days}
    reviewed_map = {d: 0 for d in days}
    for v in vocab:
        added_map[v.created_at.date()] = added_map.get(v.created_at.date(), 0) + 1
    for v in reviewed:
        reviewed_map[v.last_reviewed.date()] = reviewed_map.get(v.last_reviewed.date(), 0) + 1
    series = [{ 'date': d.strftime('%Y-%m-%d'), 'added': added_map.get(d, 0), 'reviewed': reviewed_map.get(d, 0) } for d in days]
    sub = Subscription.objects.filter(user=request.user).first()
    active = False
    if sub and sub.status == 'ACTIVE':
        active = True
    elif sub and sub.trial_end_at and sub.trial_end_at > timezone.now():
        active = True
    label = 'gold' if active else 'basic'
    total_words = Vocabulary.objects.filter(user=request.user).count()
    ctx = {
        'series': series,
        'username': request.user.username,
        'email': request.user.email,
        'date_joined': request.user.date_joined,
        'subscription_label': label,
        'total_words': total_words,
    }
    return render(request, 'users/stats.html', ctx)

@login_required
@subscription_required
@require_POST
@csrf_exempt
def save_vocabulary_view(request):
    try:
        korean_word = request.POST.get('korean_word')
        pos = request.POST.get('pos')
        grammar_info = request.POST.get('grammar_info')
        translation = request.POST.get('translation')
        
        if all([korean_word, pos, translation]):
            vocab, created = Vocabulary.objects.get_or_create(
                user=request.user,
                korean_word=korean_word,
                defaults={
                    'pos': pos,
                    'grammar_info': grammar_info or '',
                    'english_translation': translation,
                    'alpha_prior': 1.0,
                    'beta_prior': 9.0,
                    'retention_rate': 0.1
                }
            )
            
            if not created:
                vocab.pos = pos
                vocab.grammar_info = grammar_info or ''
                vocab.english_translation = translation
                vocab.save()
            else:
                vocab = update_vocabulary_recall(vocab, had_lookup=True)
                vocab.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vocabulary saved successfully',
                'created': created,
                'retention_rate': vocab.retention_rate
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_save_vocabulary(request):
    try:
        korean_word = (request.data.get('korean_word') or '').trim() if hasattr(str, 'trim') else (request.data.get('korean_word') or '').strip()
        pos = (request.data.get('pos') or '').strip()
        grammar_info = request.data.get('grammar_info') or ''
        translation = (request.data.get('translation') or '').strip()
        if not korean_word:
            return JsonResponse({'success': False, 'message': 'Missing korean_word'}, status=400)
        if not translation:
            translation = korean_word
        vocab, created = Vocabulary.objects.get_or_create(
            user=request.user,
            korean_word=korean_word,
            defaults={
                'pos': pos,
                'grammar_info': grammar_info,
                'english_translation': translation,
                'alpha_prior': 1.0,
                'beta_prior': 9.0,
                'retention_rate': 0.1
            }
        )
        if not created:
            if pos:
                vocab.pos = pos
            vocab.grammar_info = grammar_info
            if translation:
                vocab.english_translation = translation
            vocab.save()
        else:
            vocab = update_vocabulary_recall(vocab, had_lookup=True)
            vocab.save()
        return JsonResponse({'success': True, 'created': created, 'retention_rate': vocab.retention_rate})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    return JsonResponse({'success': True, 'username': request.user.username})

@login_required
def me_session(request):
    return JsonResponse({'success': True, 'username': request.user.username})

