from analysis.mecab_utils import get_papago_translation, get_sentence_translation

def translate_word(word):
	return get_papago_translation(word)

def translate_sentence(sentence):
	return get_sentence_translation(sentence)
