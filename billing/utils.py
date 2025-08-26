def is_ios_request(request):
    ua = (request.META.get('HTTP_USER_AGENT') or '').lower()
    xp = (request.META.get('HTTP_X_CLIENT_PLATFORM') or '').lower()
    return 'iphone' in ua or 'ipad' in ua or 'ipod' in ua or xp == 'ios'


