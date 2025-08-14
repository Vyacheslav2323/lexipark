from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def home_view(request):
    return redirect('analysis:analyze')

urlpatterns = [
    path('', home_view, name='home'),
    path('analysis/', include('analysis.urls', namespace='analysis')),
    path('users/', include('users.urls')),
    path('vocab/', include('vocab.urls')),
    path('billing/', include('billing.urls', namespace='billing')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
]
