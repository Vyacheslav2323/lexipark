from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import aasa_view

def home_view(request):
    return render(request, 'users/landing.html')

urlpatterns = [
    path('', home_view, name='home'),
    path('analysis/', include('analysis.urls', namespace='analysis')),
    path('users/', include('users.urls')),
    path('vocab/', include('vocab.urls')),
    path('billing/', include('billing.urls', namespace='billing')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('manifest.json', lambda request: HttpResponse(open(os.path.join(settings.BASE_DIR, 'static', 'manifest.json'), 'rb').read(), content_type='application/json')),
    path('service-worker.js', lambda request: HttpResponse(open(os.path.join(settings.BASE_DIR, 'static', 'service-worker.js'), 'rb').read(), content_type='application/javascript')),
    path("apple-app-site-association", aasa_view, name="aasa_root"),
    path(".well-known/apple-app-site-association", aasa_view, name="aasa_wk"),
]
