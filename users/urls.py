from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('save-vocabulary/', views.save_vocabulary_view, name='save_vocabulary'),
    path('api/v1/save-vocabulary/', views.api_save_vocabulary, name='api_save_vocabulary'),
    path('api/v1/me/', views.api_me, name='api_me'),
    path('api/v1/me-session/', views.me_session, name='me_session'),
    path('api/v1/login/', TokenObtainPairView.as_view(), name='api_login'),
] 