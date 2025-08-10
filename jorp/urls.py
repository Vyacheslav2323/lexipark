from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home_view(request):
    return redirect('analysis:analyze')

urlpatterns = [
    path('', home_view, name='home'),
    path('analysis/', include('analysis.urls', namespace='analysis')),
    path('users/', include('users.urls')),
    path('vocab/', include('vocab.urls')),
    path('admin/', admin.site.urls),
]
