from vocab.models import Vocabulary, GlobalTranslation
from analysis.core.translate_service import translate_word
from logger import log_error, log_tried, log_working

def get_translation(word):
	translation = ''
	try:
		log_tried(f"encounter:get_translation:{word}")
		gt = GlobalTranslation.objects.filter(korean_word=word).first()
		if gt and gt.english_translation:
			gt.usage_count += 1
			gt.save(update_fields=['usage_count'])
			log_working(f"encounter:global_translation:{word}:{gt.english_translation}")
			return gt.english_translation
		translation = translate_word(word) or ''
		if translation:
			log_working(f"encounter:translated:{word}:{translation}")
		return translation or word
	except Exception as e:
		log_error(f"encounter:translate_error:{word}:{str(e)}")
		return word

def get_user_vocab(user):
	qs = Vocabulary.objects.filter(user=user)
	return { v.korean_word: v.english_translation for v in qs }

def get_vocab_words(user):
	qs = Vocabulary.objects.filter(user=user)
	return set(qs.values_list('korean_word', flat=True))

def add_words(payload):
	user = payload['user']
	words = payload['words']
	meta = payload.get('meta') or {}
	metas = payload.get('metas') or {}
	added = []
	seen = set()
	for w in words:
		if w in seen:
			continue
		seen.add(w)
		defaults = metas.get(w) or meta
		obj, created = Vocabulary.objects.get_or_create(user=user, korean_word=w, defaults=defaults)
		if created:
			added.append(w)
	return { 'added': added }

def batch_update_recalls(payload):
	from vocab.bayesian_recall import update_vocabulary_recall
	user = payload['user']
	interactions = payload['interactions']
	updated = 0
	for word, had_lookup in interactions:
		v = Vocabulary.objects.filter(user=user, korean_word=word).first()
		if not v:
			continue
		v = update_vocabulary_recall(v, had_lookup)
		v.save()
		updated += 1
	return { 'updated': updated }

def bulk_add_words(payload):
	user = payload['user']
	words = list(payload['words'] or [])
	meta = payload.get('meta') or {}
	metas = payload.get('metas') or {}
	if not words:
		return { 'added': [] }
	existing = set(Vocabulary.objects.filter(user=user, korean_word__in=words).values_list('korean_word', flat=True))
	to_create = []
	for w in words:
		if w in existing:
			continue
		m = metas.get(w) or meta
		to_create.append(Vocabulary(
			user=user,
			korean_word=w,
			pos=m.get('pos',''),
			grammar_info=m.get('grammar_info',''),
			english_translation=m.get('english_translation', w),
			alpha_prior=10,
			beta_prior=0,
			retention_rate=1.0
		))
	if to_create:
		Vocabulary.objects.bulk_create(to_create, ignore_conflicts=True)
	return { 'added': [v.korean_word for v in to_create] }


def increment_word_encounters(payload):
	user = payload['user']
	items = list(payload.get('items') or [])
	if not items:
		return { 'updated': 0 }
	updated = 0
	for token, pos in items:
		if not token:
			continue
		v = Vocabulary.objects.filter(user=user, korean_word=token).first()
		if not v:
			v = Vocabulary.objects.create(
				user=user,
				korean_word=token,
				pos=pos or '',
				grammar_info='',
				english_translation=get_translation(token),
				in_vocab=False,
				alpha_prior=10,
				beta_prior=0,
				retention_rate=1.0
			)
		v.encounter_count = (v.encounter_count or 0) + 1
		if not v.pos:
			v.pos = pos or ''
		v.save(update_fields=['encounter_count','pos'])
		updated += 1
	return { 'updated': updated }
