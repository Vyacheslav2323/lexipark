from analysis.core.config import get_limits
from analysis.core.mecab import analyze as mecab_analyze
from analysis.core.vocab_service import get_vocab_words, get_user_vocab, add_words
from analysis.core.input_normalize import normalize_input
from analysis.mecab_utils import create_interactive_text_with_sentences
from analysis.core.interactive_rules import interactive as is_interactive

def analyze(payload):
	user = payload.get('user')
	text = normalize_input(payload)
	limits = get_limits(None)
	vocab_words = get_vocab_words(user) if user and user.is_authenticated else set()
	html = create_interactive_text_with_sentences(text, vocab_words, max_words=limits.get('max_words'))
	return { 'html': html, 'words': [] }

def finish(payload):
	user = payload.get('user')
	text = normalize_input(payload)
	limits = get_limits(None)
	results = mecab_analyze(text)
	bases = [b for (_, b, pos, _) in results if (b and is_interactive(pos))]
	seen = set()
	unique = []
	for b in bases:
		if b in seen:
			continue
		seen.add(b)
		unique.append(b)
	unique = unique[:limits.get('max_words')]
	meta = payload.get('meta') or {}
	res = add_words({ 'user': user, 'words': unique, 'meta': meta })
	return { 'added_count': len(res['added']), 'words_added': res['added'] }
