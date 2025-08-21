from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from analysis.core.pipeline import analyze as pipeline_analyze, finish as pipeline_finish

# Create your tests here.

class PipelineSmokeTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(username='u', password='p')

	def test_analyze_returns_html(self):
		res = pipeline_analyze({ 'user': self.user, 'text': '안녕하세요 저는 밥을 먹습니다.' })
		self.assertIn('html', res)
		self.assertIsInstance(res['html'], str)

	def test_finish_caps_words(self):
		text = ' '.join(['먹다'] * 1000)
		res = pipeline_finish({ 'user': self.user, 'text': text, 'meta': { 'pos': '', 'grammar_info': '', 'english_translation': '' } })
		self.assertLessEqual(res['added_count'], 150)
