from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from vocab.models import Vocabulary
from .forms import CustomUserCreationForm

# Create your views here.

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
def profile_view(request):
    vocabularies = Vocabulary.objects.filter(user=request.user)
    context = {
        'vocabularies': vocabularies,
        'total_words': vocabularies.count()
    }
    return render(request, 'users/profile.html', context)

@login_required
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
                    'english_translation': translation
                }
            )
            
            if not created:
                vocab.pos = pos
                vocab.grammar_info = grammar_info or ''
                vocab.english_translation = translation
                vocab.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vocabulary saved successfully',
                'created': created
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
