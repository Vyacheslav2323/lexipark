from django.urls import path
from .views import analyze_view, track_hover, track_sentence_hover, process_photo_ocr, image_analysis_view, real_life_subtitles_view
from .api import analyze_api, finish_api, batch_recall_api, translate_word_api, translate_sentence_api, analyze_sentence_api, finish_sentence_api, finish_batch_api
from .api import transcribe_api

app_name = 'analysis'

urlpatterns = [
    path('page1/', analyze_view, name='analyze'),
    path('image-analysis/', image_analysis_view, name='image_analysis'),
    path('real-subtitles/', real_life_subtitles_view, name='real_subtitles'),

    path('track-hover/', track_hover, name='track_hover'),
    path('track-sentence-hover/', track_sentence_hover, name='track_sentence_hover'),
    path('process-photo-analysis/', process_photo_ocr, name='process_photo_analysis'),
    path('api/analyze', analyze_api, name='analyze_api'),
    path('api/v1/analyze/', analyze_api, name='analyze_api_v1'),
    path('api/analyze-sentence', analyze_sentence_api, name='analyze_sentence_api'),
    path('api/finish', finish_api, name='finish_api'),
    path('api/finish-batch', finish_batch_api, name='finish_batch_api'),
    path('api/transcribe', transcribe_api, name='transcribe'),
    path('api/finish-sentence', finish_sentence_api, name='finish_sentence_api'),
    path('api/batch-recall', batch_recall_api, name='batch_recall_api'),
    path('api/translate-word', translate_word_api, name='translate_word_api'),
    path('api/translate-sentence', translate_sentence_api, name='translate_sentence_api'),
] 