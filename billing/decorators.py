from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.timezone import now
from .models import Subscription


def subscription_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login') if request.method == 'GET' else JsonResponse({'success': False, 'error': 'Auth required'}, status=401)
        sub = Subscription.objects.filter(user=request.user).first()
        if not sub:
            return JsonResponse({'success': False, 'error': 'Subscription required', 'code': 'NO_SUB'}, status=402) if request.method != 'GET' else redirect('billing:get_gold')
        if sub.status == 'ACTIVE':
            return view_func(request, *args, **kwargs)
        if sub.trial_end_at and sub.trial_end_at > now():
            return view_func(request, *args, **kwargs)
        return JsonResponse({'success': False, 'error': 'Subscription inactive', 'code': 'INACTIVE'}, status=402) if request.method != 'GET' else redirect('billing:get_gold')
    return _wrapped


