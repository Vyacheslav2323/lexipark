class StripAuthForAnalysisMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        p = request.path or ''
        if p.startswith('/analysis/api/'):
            if 'HTTP_AUTHORIZATION' in request.META:
                request.META.pop('HTTP_AUTHORIZATION', None)
        return self.get_response(request)



