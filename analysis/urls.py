from django.urls import path
from .views import analyze_view, track_hover, track_sentence_hover, batch_update_recalls_view, analyze_ajax, finish_analysis_ajax

urlpatterns = [
    path('page1/', analyze_view, name='analyze'),
    path('analyze-ajax/', analyze_ajax, name='analyze_ajax'),
    path('finish-analysis-ajax/', finish_analysis_ajax, name='finish_analysis_ajax'),
    path('track-hover/', track_hover, name='track_hover'),
    path('track-sentence-hover/', track_sentence_hover, name='track_sentence_hover'),
    path('batch-update-recalls/', batch_update_recalls_view, name='batch_update_recalls'),
] 