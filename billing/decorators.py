from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.timezone import now
from datetime import timedelta
from .models import Subscription
from .utils import is_ios_request


def subscription_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login') if request.method == 'GET' else JsonResponse({'success': False, 'error': 'Auth required'}, status=401)
        if is_ios_request(request):
            return view_func(request, *args, **kwargs)
        sub = Subscription.objects.filter(user=request.user).first()
        if not sub:
            sub = Subscription.objects.create(user=request.user, status='NONE', trial_end_at=now() + timedelta(days=7))
        if sub.status == 'ACTIVE':
            return view_func(request, *args, **kwargs)
        if sub.trial_end_at and sub.trial_end_at > now():
            return view_func(request, *args, **kwargs)
        return JsonResponse({'success': False, 'error': 'Subscription inactive', 'code': 'INACTIVE'}, status=402) if request.method != 'GET' else redirect('billing:get_gold')
    return _wrapped


