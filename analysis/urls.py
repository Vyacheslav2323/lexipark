from django.urls import path
from .views import analyze_view, track_hover, track_sentence_hover

urlpatterns = [
    path('page1/', analyze_view, name='analyze'),
    path('track-hover/', track_hover, name='track_hover'),
    path('track-sentence-hover/', track_sentence_hover, name='track_sentence_hover'),
] 