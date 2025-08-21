import os
import json
from datetime import datetime, timedelta, timezone
import requests
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime
from urllib.parse import urlparse, urlunparse
from .models import Subscription, PromoCode, PromoRedemption
from django.shortcuts import render
import logging

logger = logging.getLogger('billing')


def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def grant_free_access(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_identifier = data.get('user_identifier')
        access_type = data.get('access_type', 'trial')
        trial_days = data.get('trial_days', 30)
        
        if not user_identifier:
            return JsonResponse({'success': False, 'error': 'user_identifier required'}, status=400)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if '@' in user_identifier:
            user = User.objects.get(email=user_identifier)
        else:
            user = User.objects.get(username=user_identifier)
        
        sub, created = Subscription.objects.get_or_create(user=user)
        
        if access_type == 'lifetime':
            sub.lifetime_free = True
            sub.status = 'ACTIVE'
            message = f'Granted lifetime free access to {user.username}'
        else:
            from django.utils.timezone import now
            trial_extension = now() + timedelta(days=trial_days)
            sub.trial_end_at = trial_extension
            message = f'Extended trial for {user.username} by {trial_days} days'
        
        sub.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'user': {
                'username': user.username,
                'email': user.email
            },
            'subscription': {
                'lifetime_free': sub.lifetime_free,
                'trial_end_at': sub.trial_end_at.isoformat() if sub.trial_end_at else None,
                'status': sub.status
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'User not found: {user_identifier}'}, status=404)
    except Exception as e:
        logger.error(f'Error granting free access: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@user_passes_test(is_admin)
def revoke_free_access(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_identifier = data.get('user_identifier')
        
        if not user_identifier:
            return JsonResponse({'success': False, 'error': 'user_identifier required'}, status=400)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if '@' in user_identifier:
            user = User.objects.get(email=user_identifier)
        else:
            user = User.objects.get(username=user_identifier)
        
        try:
            sub = Subscription.objects.get(user=user)
            sub.lifetime_free = False
            sub.save()
            message = f'Revoked lifetime free access from {user.username}'
        except Subscription.DoesNotExist:
            message = f'No subscription found for {user.username}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'user': {
                'username': user.username,
                'email': user.email
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'User not found: {user_identifier}'}, status=404)
    except Exception as e:
        logger.error(f'Error revoking free access: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _paypal_base():
    return 'https://api-m.sandbox.paypal.com' if os.getenv('PAYPAL_MODE', 'sandbox') == 'sandbox' else 'https://api-m.paypal.com'


def _paypal_token():
    cid = os.getenv('PAYPAL_CLIENT_ID')
    secret = os.getenv('PAYPAL_SECRET')
    logger.info('paypal.token.request')
    r = requests.post(
        f"{_paypal_base()}/v1/oauth2/token",
        auth=(cid, secret),
        data={ 'grant_type': 'client_credentials' },
        headers={ 'Accept': 'application/json' }
    )
    r.raise_for_status()
    logger.info('paypal.token.ok')
    return r.json()['access_token']


def _get_headers(token):
    return { 'Content-Type': 'application/json', 'Authorization': f'Bearer {token}' }


def _ensure_product(access_token):
    h = _get_headers(access_token)
    try:
        lr = requests.get(f"{_paypal_base()}/v1/catalogs/products?page_size=20&total_required=true", headers=h)
        lr.raise_for_status()
        for p in lr.json().get('products', []):
            if p.get('name') == 'LexiPark Premium':
                logger.info('paypal.product.reuse id=%s', p.get('id'))
                return p.get('id')
    except Exception:
        pass
    payload = { 'name': 'LexiPark Premium', 'type': 'SERVICE', 'category': 'SOFTWARE' }
    pr = requests.post(f"{_paypal_base()}/v1/catalogs/products", headers={ **h, 'PayPal-Request-Id': str(uuid.uuid4()) }, data=json.dumps(payload))
    pr.raise_for_status()
    logger.info('paypal.product.created id=%s', pr.json().get('id'))
    return pr.json()['id']


def _find_plan(access_token, product_id, price_value):
    h = _get_headers(access_token)
    try:
        lr = requests.get(f"{_paypal_base()}/v1/billing/plans?product_id={product_id}&page_size=20&status=ACTIVE", headers=h)
        lr.raise_for_status()
        for plan in lr.json().get('plans', []):
            for bc in plan.get('billing_cycles', []):
                if bc.get('tenure_type') == 'REGULAR':
                    fp = (bc.get('pricing_scheme') or {}).get('fixed_price') or {}
                    if fp.get('currency_code') == 'KRW' and fp.get('value') == str(price_value):
                        logger.info('paypal.plan.found id=%s price=%sKRW', plan.get('id'), price_value)
                        return plan.get('id')
    except Exception:
        return None
    return None


def _create_plan(access_token, product_id, price_value):
    h = _get_headers(access_token)
    name = f"LexiPark Monthly KRW {price_value}"
    payload = {
        'product_id': product_id,
        'name': name,
        'status': 'ACTIVE',
        'billing_cycles': [
            { 'frequency': { 'interval_unit': 'DAY', 'interval_count': 7 }, 'tenure_type': 'TRIAL', 'sequence': 1, 'total_cycles': 1, 'pricing_scheme': { 'fixed_price': { 'value': '0', 'currency_code': 'KRW' } } },
            { 'frequency': { 'interval_unit': 'MONTH', 'interval_count': 1 }, 'tenure_type': 'REGULAR', 'sequence': 2, 'total_cycles': 0, 'pricing_scheme': { 'fixed_price': { 'value': str(price_value), 'currency_code': 'KRW' } } }
        ],
        'payment_preferences': { 'auto_bill_outstanding': True, 'payment_failure_threshold': 1 }
    }
    rrid = str(uuid.uuid4())
    r = requests.post(f"{_paypal_base()}/v1/billing/plans", headers={ **h, 'PayPal-Request-Id': rrid }, data=json.dumps(payload))
    if r.status_code == 422:
        pid = _find_plan(access_token, product_id, price_value)
        if pid:
            logger.info('paypal.plan.reused_after_422 id=%s price=%s', pid, price_value)
            return pid
    r.raise_for_status()
    logger.info('paypal.plan.created id=%s price=%s', r.json().get('id'), price_value)
    return r.json()['id']


def _ensure_plan_for_price(access_token, price_value):
    env_key = 'PAYPAL_PLAN_ID_9999' if str(price_value) == '9999' else os.getenv('PAYPAL_PLAN_ID')
    if isinstance(env_key, str) and env_key and str(price_value) == '9999':
        return os.getenv('PAYPAL_PLAN_ID_9999')
    if isinstance(env_key, str) and env_key and str(price_value) != '9999':
        return env_key
    product_id = _ensure_product(access_token)
    existing = _find_plan(access_token, product_id, price_value)
    if existing:
        return existing
    return _create_plan(access_token, product_id, price_value)


def _ensure_discount_plan(access_token):
    return _ensure_plan_for_price(access_token, 9999)


@login_required
def subscription_status(request):
    sub = Subscription.objects.filter(user=request.user).first()
    if not sub:
        return JsonResponse({ 'active': False })
    return JsonResponse({
        'active': sub.is_active(),
        'status': sub.status,
        'trial_end_at': sub.trial_end_at.isoformat() if sub.trial_end_at else None,
        'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
        'lifetime_free': sub.lifetime_free,
    })


@login_required
def create_subscription(request):
    user = request.user
    logger.info('subscription.create.start user=%s', user.id)
    token = _paypal_token()
    sub = Subscription.objects.filter(user=user).first()
    plan_id = None
    env_regular = os.getenv('PAYPAL_PLAN_ID') or ''
    env_discount = os.getenv('PAYPAL_PLAN_ID_9999') or ''
    stored = sub.discount_plan_id if sub and sub.discount_plan_id else ''
    stored_valid = bool(stored) and stored.startswith('P-')
    has_discount = PromoRedemption.objects.filter(user=user, promo__kind=PromoCode.KIND_DISCOUNT_9999).exists() or stored_valid

    if has_discount:
        if env_discount.startswith('P-'):
            plan_id = env_discount
            logger.info('subscription.create.plan.source env_discount plan_id=%s', plan_id)
        elif stored_valid:
            plan_id = stored
            logger.info('subscription.create.plan.source stored_discount plan_id=%s', plan_id)
        else:
            plan_id = _ensure_discount_plan(token)
            logger.info('subscription.create.plan.source ensured_discount plan_id=%s', plan_id)
            if sub:
                sub.discount_plan_id = plan_id
                sub.save(update_fields=['discount_plan_id'])
    else:
        if env_regular.startswith('P-'):
            plan_id = env_regular
            logger.info('subscription.create.plan.source env_regular plan_id=%s', plan_id)
        else:
            plan_id = _ensure_plan_for_price(token, 15000)
            logger.info('subscription.create.plan.source ensured_regular plan_id=%s', plan_id)

    if sub and stored and not stored_valid:
        sub.discount_plan_id = None
        sub.save(update_fields=['discount_plan_id'])

    logger.info('subscription.create.plan plan_id=%s user=%s', plan_id, user.id)
    return_url = request.build_absolute_uri('/users/profile/')
    cancel_url = request.build_absolute_uri('/users/profile/')
    mode = os.getenv('PAYPAL_MODE', 'sandbox').lower()
    if mode == 'live':
        def _https(u):
            p = urlparse(u)
            scheme = 'https'
            netloc = p.netloc
            return urlunparse((scheme, netloc, p.path, p.params, p.query, p.fragment))
        return_url = _https(return_url)
        cancel_url = _https(cancel_url)
    logger.info('subscription.create.urls return=%s cancel=%s', return_url, cancel_url)
    payload = {
        'plan_id': plan_id,
        'application_context': {
            'brand_name': 'LexiPark',
            'locale': 'en-US',
            'shipping_preference': 'NO_SHIPPING',
            'user_action': 'SUBSCRIBE_NOW',
            'return_url': return_url,
            'cancel_url': cancel_url
        }
    }
    try:
        r = requests.post(
            f"{_paypal_base()}/v1/billing/subscriptions",
            headers={ 'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {token}' },
            data=json.dumps(payload)
        )
        r.raise_for_status()
        data = r.json()
    except requests.HTTPError as e:
        body = None
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text if e.response is not None else str(e)
        logger.error('subscription.create.error status=%s details=%s', getattr(e.response, 'status_code', None), body)
        return JsonResponse({ 'success': False, 'error': 'paypal_subscription_create_failed', 'details': body }, status=e.response.status_code if e.response is not None else 500)
    approve = next((l['href'] for l in data.get('links', []) if l.get('rel') == 'approve'), None)
    sub, _ = Subscription.objects.get_or_create(user=user)
    sub.plan_id = plan_id
    sub.paypal_subscription_id = data.get('id')
    sub.status = data.get('status', 'APPROVAL_PENDING')
    if not sub.trial_end_at:
        sub.trial_end_at = datetime.now(timezone.utc) + timedelta(days=7)
    sub.save()
    logger.info('subscription.create.ok id=%s user=%s', data.get('id'), user.id)
    return JsonResponse({ 'approval_url': approve, 'id': data.get('id') })


@csrf_exempt
def webhook(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False}, status=400)
    event_type = data.get('event_type')
    logger.info('webhook.event %s', event_type)
    resource = data.get('resource', {})
    sub_id = resource.get('id') or resource.get('subscription_id')
    sub = Subscription.objects.filter(paypal_subscription_id=sub_id).first()
    if not sub:
        return JsonResponse({'success': True})
    if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
        sub.status = 'ACTIVE'
        billing_info = resource.get('billing_info') or {}
        next_billing_time = billing_info.get('next_billing_time')
        if next_billing_time:
            dt = parse_datetime(next_billing_time)
            sub.current_period_end = dt
        create_time = resource.get('create_time')
        if create_time and not sub.trial_end_at:
            dt = parse_datetime(create_time)
            sub.trial_end_at = dt + timedelta(days=7)
        sub.save()
    elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
        sub.status = 'CANCELLED'
        sub.save()
    elif event_type == 'PAYMENT.SALE.COMPLETED':
        billing_info = resource.get('billing_agreement_details') or {}
        next_billing_time = billing_info.get('next_billing_date')
        if next_billing_time:
            try:
                dt = parse_datetime(next_billing_time)
            except Exception:
                dt = None
            if dt:
                sub.current_period_end = dt
                sub.status = 'ACTIVE'
                sub.save()
    return JsonResponse({'success': True})


@login_required
def get_gold_page(request):
    sub = Subscription.objects.filter(user=request.user).first()
    active = False
    if sub and sub.status == 'ACTIVE':
        active = True
    elif sub and sub.trial_end_at and sub.trial_end_at > datetime.now(timezone.utc):
        active = True
    has_discount = False
    if sub and sub.discount_plan_id:
        has_discount = True
    else:
        has_discount = PromoRedemption.objects.filter(user=request.user, promo__kind=PromoCode.KIND_DISCOUNT_9999).exists()
    mode = os.getenv('PAYPAL_MODE', 'sandbox').lower()
    currency = os.getenv('PAYPAL_CURRENCY') or ('USD' if mode == 'live' else 'KRW')
    pr_def = '10.99' if currency == 'USD' else '15000'
    pd_def = '6.99' if currency == 'USD' else '9999'
    pr_env = os.getenv('PAYPAL_PRICE_REGULAR') or pr_def
    pd_env = os.getenv('PAYPAL_PRICE_DISCOUNT') or pd_def
    price_str = pd_env if has_discount else pr_env
    return render(request, 'billing/get_gold.html', { 'active': active, 'display_currency': currency, 'display_price': price_str })


@login_required
@csrf_exempt
def redeem_promo(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        code = (data.get('code') or '').strip()
        if not code:
            return JsonResponse({'success': False, 'error': 'Missing code'}, status=400)
        promo = PromoCode.objects.filter(code__iexact=code, used_at__isnull=True).first()
        if promo and promo.assigned_user and promo.assigned_user_id != request.user.id:
            return JsonResponse({'success': False, 'error': 'Invalid code'}, status=404)
        if not promo:
            return JsonResponse({'success': False, 'error': 'Invalid code'}, status=404)
        if PromoRedemption.objects.filter(promo=promo, user=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Code already used'}, status=400)
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        if promo.kind == PromoCode.KIND_LIFETIME_FREE:
            sub.lifetime_free = True
            sub.status = 'ACTIVE'
            sub.save()
        elif promo.kind == PromoCode.KIND_DISCOUNT_9999:
            pass
        PromoRedemption.objects.create(promo=promo, user=request.user)
        logger.info('promo.redeem.ok code=%s user=%s kind=%s', promo.code, request.user.id, promo.kind)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error('promo.redeem.error %s', str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@user_passes_test(is_admin)
def admin_free_access_page(request):
    return render(request, 'billing/admin_free_access.html')


