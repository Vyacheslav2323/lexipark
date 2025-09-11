import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from billing.decorators import subscription_required
from analysis.core.pipeline import analyze as pipeline_analyze, finish as pipeline_finish
from analysis.core.vocab_service import batch_update_recalls, bulk_add_words, increment_word_encounters
from analysis.core.translate_service import translate_word as svc_translate_word, translate_sentence as svc_translate_sentence
from analysis.mecab_utils import analyze_sentence as mecab_analyze_sentence, create_interactive_sentence
from vocab.models import Vocabulary, GlobalTranslation
from django.core.cache import cache
import hashlib
from analysis.core.interactive_rules import interactive as is_interactive
import os
import subprocess
import tempfile
import tempfile
import base64
import requests

def _resolve_user(request):
	user = getattr(request, 'user', None)
	if user and getattr(user, 'is_authenticated', False):
		return user
	try:
		from rest_framework_simplejwt.authentication import JWTAuthentication
		auth = JWTAuthentication()
		h = request.META.get('HTTP_AUTHORIZATION', '') or ''
		p = h.split()
		if len(p) == 2 and p[0].lower() == 'bearer':
			vt = auth.get_validated_token(p[1])
			return auth.get_user(vt)
	except Exception:
		return user
	return user

@csrf_exempt
def analyze_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body or '{}')
		text = data.get('text') or ''
		user = _resolve_user(request)
		has_auth = bool((request.META.get('HTTP_AUTHORIZATION') or '').strip())
		try:
			vc = Vocabulary.objects.filter(user=user).count() if user and getattr(user, 'id', None) else 0
		except Exception:
			vc = -1
		print(f"analyze_api: has_auth={has_auth} uid={(getattr(user,'id',0) or 0)} vocab_count={vc}")
		if not (user and getattr(user, 'is_authenticated', False)):
			return JsonResponse({ 'success': True, 'html': '', 'words': [] })
		uid = getattr(user, 'id', 0) or 0
		key = f"analyze:{uid}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
		res = cache.get(key)
		if not res:
			res = pipeline_analyze({ 'user': user, 'text': text })
			cache.set(key, res, 60)
		# increment encounters for webext usage too
		try:
			if user and getattr(user, 'is_authenticated', False):
				from analysis.core.mecab import analyze as mecab_analyze
				results = mecab_analyze(text)
				items = []
				for (_, b, pos, _) in results:
					if b:
						items.append((b, pos or ''))
				if items:
					increment_word_encounters({ 'user': user, 'items': items })
		except Exception:
			pass
		return JsonResponse({ 'success': True, **res })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@subscription_required
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
@subscription_required
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
			try:
				if request.user and request.user.is_authenticated:
					items = []
					for (surface, base, pos, _) in results:
						if base:
							items.append((base, pos or ''))
					if items:
						increment_word_encounters({ 'user': request.user, 'items': items })
			except Exception:
				pass
			translations = []
			for _, base, _, _ in results:
				translations.append(vocab_map.get(base, '') if base else None)
			html = create_interactive_sentence(sentence, results, translations, vocab_words)
			cache.set(key, html, 60)
		return JsonResponse({ 'success': True, 'html': html })
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@subscription_required
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
@subscription_required
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

def _parse_text_json(s):
	try:
		obj = json.loads(s)
		if isinstance(obj, dict):
			if 'result' in obj and isinstance(obj['result'], dict):
				return obj['result'].get('text') or obj['result'].get('msg') or s
			return obj.get('text') or obj.get('msg') or obj.get('message') or s
		return s
	except Exception:
		return s

def _convert_to_pcm(d):
	try:
		raw = d.get('raw') or b''
		src = (d.get('src_mime') or '').lower()
		if len(raw) < 2000:
			return { 'ok': False, 'error': 'audio too short' }
		ff = os.getenv('FFMPEG_BIN', 'ffmpeg')
		cmd = [ff, '-y', '-i', 'pipe:0', '-ac', '1', '-ar', '16000', '-f', 's16le', '-acodec', 'pcm_s16le', 'pipe:1']
		p = subprocess.run(cmd, input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
		if p.returncode != 0:
			return { 'ok': False, 'error': 'ffmpeg convert failed' }
		pcm = p.stdout or b''
		if len(pcm) < 2000:
			return { 'ok': False, 'error': 'audio too short after convert' }
		return { 'ok': True, 'pcm': pcm }
	except Exception as e:
		return { 'ok': False, 'error': str(e) }

def _grpc_transcribe(d):
	try:
		pcm = d.get('pcm') or b''
		import grpc
		import nest_pb2 as pb
		import nest_pb2_grpc as pbg
		key = (os.getenv('CLOVASPEECH_API_KEY') or '').strip()
		if not key:
			return { 'ok': False, 'error': 'missing api key' }
		hp = os.getenv('CLOVA_GRPC', 'clovaspeech-gw.ncloud.com:50051')
		cfg = json.dumps({ 'language': os.getenv('CLOVA_LANG','ko-KR'), 'sampleRate': 16000, 'encoding': 'LINEAR16', 'interimResults': True })
		def _iter():
			yield pb.NestRequest(type=pb.CONFIG, config=pb.NestConfig(config=cfg))
			yield pb.NestRequest(type=pb.DATA, data=pb.NestData(chunk=pcm))
		creds = grpc.ssl_channel_credentials()
		stub = pbg.NestServiceStub(grpc.secure_channel(hp, creds))
		meta = (('x-clovaspeech-api-key', key),)
		text = ''
		last = ''
		for r in stub.recognize(_iter(), metadata=meta):
			m = _parse_text_json(r.contents)
			if isinstance(m, str) and m.strip():
				last = m
			if any(k in r.contents for k in ['"isFinal":true','"is_final":true']):
				text = m
		if (text or last):
			return { 'ok': True, 'text': (text or last) }
		return { 'ok': False, 'error': 'no speech' }
	except Exception as e:
		return { 'ok': False, 'error': str(e) }

@csrf_exempt
@login_required
@subscription_required
def transcribe_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
	try:
		audio = request.FILES.get('audio')
		if not audio:
			return JsonResponse({'success': False, 'error': 'Missing audio'}, status=400)

		raw = audio.read()
		src_mime = (audio.content_type or '').lower()
		try:
			print(f"transcribe_api: content_type={src_mime} size={len(raw)} name={getattr(audio,'name','')}")
		except Exception:
			pass
		if len(raw) < 2000:
			return JsonResponse({'success': False, 'error': 'audio too short; send >= 0.5s'}, status=400)


		url = (os.getenv('CLOVA_SPEECH_INVOKE_URL') or '').strip()
		api_key = (os.getenv('CLOVASPEECH_API_KEY') or '').strip()
		if not url or not api_key:
			return JsonResponse({'success': False, 'error': 'Set CLOVA_SPEECH_INVOKE_URL and CLOVASPEECH_API_KEY'}, status=400)

		if any(t in src_mime for t in ['mp4','m4a','aac','webm','ogg','mp3']):
			ff = os.getenv('FFMPEG_BIN', 'ffmpeg')
			with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as out_f:
				cmd = [ff, '-y', '-i', 'pipe:0', '-ac', '1', '-ar', '16000', '-acodec', 'pcm_s16le', out_f.name]
				p = subprocess.run(cmd, input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
				if p.returncode != 0:
					err = (p.stderr or b'')[:800].decode('utf-8', 'ignore')
					return JsonResponse({'success': False, 'error': 'ffmpeg convert failed', 'stderr': err}, status=400)
				out_f.seek(0)
				raw = out_f.read()
				if len(raw) < 2000:
					return JsonResponse({'success': False, 'error': 'audio too short after convert; send >= 0.5s'}, status=400)

		payload = {
			'language': 'ko-KR',
			'completion': 'sync',
			'transcription': 'srt',
			'audio': {
				'format': 'wav',
				'sampleRate': 16000,
				'channels': 1,
				'data': base64.b64encode(raw).decode('ascii')
			}
		}
		headers = {
			'X-CLOVASPEECH-API-KEY': api_key,
			'Content-Type': 'application/json',
			'Accept': 'application/json'
		}
		r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=90)
		if r.status_code != 200:
			return JsonResponse({'success': False, 'error': f'CLOVA HTTP {r.status_code}', 'body': r.text[:800]}, status=502)
		data = r.json()
		def _strip_srt(s):
			try:
				lines = []
				for ln in (s.split('\n')):
					l = ln.strip()
					if not l or l.isdigit() or ('-->' in l):
						continue
					lines.append(l)
				return ' '.join(lines)
			except Exception:
				return s
		def _extract_text(obj):
			if isinstance(obj, str):
				return _strip_srt(obj) if ('-->' in obj or '\n' in obj) else obj
			if isinstance(obj, dict):
				out = []
				for v in obj.values():
					t = _extract_text(v)
					if t:
						out.append(t)
				return ' '.join([t for t in out if isinstance(t, str)])
			if isinstance(obj, list):
				out = []
				for v in obj:
					t = _extract_text(v)
					if t:
						out.append(t)
				return ' '.join([t for t in out if isinstance(t, str)])
			return ''
		text = data.get('text') or data.get('result') or ''
		if not text:
			text = _extract_text(data)
		text = (text or '').strip()
		return JsonResponse({'success': True, 'text': (text or '').strip()})
	except Exception as e:
		print(f"transcribe_api: exception: {e}")
		return JsonResponse({'success': False, 'error': str(e)}, status=500)
