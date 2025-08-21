from analysis.mecab_utils import create_interactive_sentence, translate_results
from analysis.core.interactive_rules import interactive

def build_html(payload):
	sentence = payload['sentence']
	results = payload['results']
	vocab_words = payload.get('vocab_words') or set()
	translations = translate_results(results)
	return create_interactive_sentence(sentence, results, translations, vocab_words)

def build_words_json(payload):
	results = payload['results']
	vocab_map = payload.get('vocab_map') or {}
	words = []
	for surface, base, pos, grammar_info in results:
		if base is None:
			continue
		words.append({
			'surface': surface,
			'base': base,
			'pos': pos,
			'grammar_info': grammar_info,
			'translation': vocab_map.get(base),
			'in_vocab': base in (vocab_map.keys())
		})
	return words
