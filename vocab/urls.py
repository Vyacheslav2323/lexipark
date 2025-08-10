from django.urls import path
from . import views

app_name = 'vocab'

urlpatterns = [
    path('test/', views.vocabulary_test, name='vocabulary_test'),
]
