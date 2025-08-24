import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from analysis.core.pipeline import analyze as pipeline_analyze, finish as pipeline_finish
from analysis.core.vocab_service import batch_update_recalls, bulk_add_words
from analysis.core.translate_service import translate_word as svc_translate_word, translate_sentence as svc_translate_sentence
from analysis.mecab_utils import analyze_sentence as mecab_analyze_sentence, create_interactive_sentence
from vocab.models import Vocabulary, GlobalTranslation
from django.core.cache import cache
import hashlib
from analysis.core.interactive_rules import interactive as is_interactive

@csrf_exempt
def analyze_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		text = data.get('text') or ''
		# Resolve user before caching so cache key is user-aware
		user = request.user
		if not (user and getattr(user, 'is_authenticated', False)):
			from rest_framework_simplejwt.authentication import JWTAuthentication
			try:
				auth = JWTAuthentication()
				validated = auth.authenticate(request)
				if validated and validated[0]:
					user = validated[0]
			except Exception:
				user = request.user
		uid = getattr(user, 'id', 0) or 0
		key = f"analyze:{uid}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
		res = cache.get(key)
		if not res:
			res = pipeline_analyze({ 'user': user, 'text': text })
			cache.set(key, res, 60)
		return JsonResponse({ 'success': True, **res })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def finish_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		text = data.get('text') or ''
		res = pipeline_finish({ 'user': request.user, 'text': text, 'meta': { 'pos': '', 'grammar_info': '', 'english_translation': '' } })
		msg = f"Added {res.get('added_count', 0)} words to vocabulary"
		return JsonResponse({ 'success': True, 'message': msg, **res })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def batch_recall_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		interactions = data.get('interactions') or []
		res = batch_update_recalls({ 'user': request.user, 'interactions': interactions })
		return JsonResponse({ 'success': True, 'updated_count': res['updated'] })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def translate_word_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		word = data.get('word') or ''
		tr = svc_translate_word(word)
		return JsonResponse({ 'success': True, 'translation': tr })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def translate_sentence_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		sentence = data.get('sentence') or ''
		tr = svc_translate_sentence(sentence)
		return JsonResponse({ 'success': True, 'translation': tr })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def analyze_sentence_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		sentence = data.get('sentence') or ''
		if not sentence.strip():
			return JsonResponse({'success': False, 'error': 'Empty sentence'})
		uid = getattr(request.user, 'id', 0) or 0
		key = f"analyze_sentence:{uid}:{hashlib.sha256(sentence.encode('utf-8')).hexdigest()}"
		html = cache.get(key)
		if not html:
			vocab_words = set()
			vocab_map = {}
			if request.user and request.user.is_authenticated:
				qs = Vocabulary.objects.filter(user=request.user)
				vocab_words = set(qs.values_list('korean_word', flat=True))
				vocab_map = {v.korean_word: v.english_translation for v in qs}
			results = mecab_analyze_sentence(sentence)
			translations = []
			for _, base, _, _ in results:
				translations.append(vocab_map.get(base, '') if base else None)
			html = create_interactive_sentence(sentence, results, translations, vocab_words)
			cache.set(key, html, 60)
		return JsonResponse({ 'success': True, 'html': html })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def finish_sentence_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		sentence = data.get('sentence') or ''
		if not sentence.strip():
			return JsonResponse({'success': False, 'error': 'Empty sentence'})
		res = pipeline_finish({ 'user': request.user, 'text': sentence, 'meta': { 'pos': '', 'grammar_info': '', 'english_translation': '' } })
		return JsonResponse({ 'success': True, **res })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def finish_batch_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		sentences = data.get('sentences') or []
		if not isinstance(sentences, list) or not sentences:
			return JsonResponse({'success': False, 'error': 'No sentences'})
		from analysis.core.mecab import analyze as mecab_analyze
		bases = []
		metas = {}
		for s in sentences:
			for (surface, b, pos, grammar_info) in mecab_analyze(s):
				if not b or not is_interactive(pos):
					continue
				bases.append(b)
				if b not in metas:
					metas[b] = { 'pos': pos or '', 'grammar_info': grammar_info or '', 'english_translation': b }
		# fill translations from global cache if present
		if bases:
			unique_bases = list(dict.fromkeys(bases))
			gt_map = { g.korean_word: g.english_translation for g in GlobalTranslation.objects.filter(korean_word__in=unique_bases) }
			for k in unique_bases:
				if k in metas and gt_map.get(k):
					metas[k]['english_translation'] = gt_map[k]
		seen = set()
		unique = []
		for b in bases:
			if b in seen:
				continue
			seen.add(b)
			unique.append(b)
		existing = set(Vocabulary.objects.filter(user=request.user, korean_word__in=unique).values_list('korean_word', flat=True))
		to_add = [w for w in unique if w not in existing]
		res = bulk_add_words({ 'user': request.user, 'words': to_add, 'meta': { 'pos':'', 'grammar_info':'', 'english_translation':'' }, 'metas': metas })
		return JsonResponse({ 'success': True, 'attempted_count': len(unique), 'added_count': len(res['added']), 'skipped_existing': len(existing), 'words_added': res['added'] })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)
