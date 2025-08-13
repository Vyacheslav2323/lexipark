from django.urls import path
from .views import analyze_view, track_hover, track_sentence_hover, finish_analysis_view, batch_update_recalls_view, translate_sentence, process_photo_ocr, image_analysis_view, analyze_ocr_text, analyze_sentence_chunk, translate_word, api_analyze_text, api_analyze_html

app_name = 'analysis'

urlpatterns = [
    path('page1/', analyze_view, name='analyze'),
    path('image-analysis/', image_analysis_view, name='image_analysis'),

    path('track-hover/', track_hover, name='track_hover'),
    path('track-sentence-hover/', track_sentence_hover, name='track_sentence_hover'),
    path('finish-analysis/', finish_analysis_view, name='finish_analysis'),
    path('batch-update-recalls/', batch_update_recalls_view, name='batch_update_recalls'),
    path('translate-sentence/', translate_sentence, name='translate_sentence'),
    path('analyze-sentence/', analyze_sentence_chunk, name='analyze_sentence'),
    path('translate-word/', translate_word, name='translate_word'),
    path('process-photo-analysis/', process_photo_ocr, name='process_photo_analysis'),
    path('analyze-ocr-text/', analyze_ocr_text, name='analyze_ocr_text'),
    path('api/v1/analyze/', api_analyze_text, name='api_analyze_text'),
    path('api/v1/analyze-html/', api_analyze_html, name='api_analyze_html'),
] 