from django.urls import path
from .views import analyze_view, track_hover, track_sentence_hover, batch_update_recalls_view, health_check, finish_analysis_view

urlpatterns = [
    path('page1/', analyze_view, name='analyze'),
    path('track-hover/', track_hover, name='track_hover'),
    path('track-sentence-hover/', track_sentence_hover, name='track_sentence_hover'),
    path('batch-update-recalls/', batch_update_recalls_view, name='batch_update_recalls'),
    path('finish-analysis/', finish_analysis_view, name='finish_analysis'),
    path('health/', health_check, name='health_check'),
] 