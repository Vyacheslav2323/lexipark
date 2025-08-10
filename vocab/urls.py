from django.urls import path
from . import views

app_name = 'vocab'

urlpatterns = [
    path('test/', views.vocabulary_test, name='vocabulary_test'),
    path('test/ranks/', views.get_test_ranks, name='get_test_ranks'),
    path('test/update-alpha/', views.update_alpha_prior, name='update_alpha_prior'),
    path('test/batch-update/', views.batch_update_adaptive, name='batch_update_adaptive'),
]
