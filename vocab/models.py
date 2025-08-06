from django.db import models
from django.contrib.auth.models import User
import json

class Grammar(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class GlobalTranslation(models.Model):
    korean_word = models.CharField(max_length=100, unique=True)
    english_translation = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-usage_count', '-created_at']
    
    def __str__(self):
        return f"{self.korean_word} -> {self.english_translation} (used {self.usage_count} times)"

class Vocabulary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vocabularies')
    korean_word = models.CharField(max_length=100)
    pos = models.CharField(max_length=20, default='')
    grammar_info = models.TextField(blank=True)
    english_translation = models.CharField(max_length=200)
    hover_count = models.IntegerField(default=0)
    total_hover_time = models.FloatField(default=0.0)
    last_5_durations = models.TextField(default='[]')
    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed = models.DateTimeField(auto_now=True)
    grammars = models.ManyToManyField(Grammar, blank=True, related_name='vocabularies')
    retention_rate = models.FloatField(default=0.1)
    last_recall_update = models.DateTimeField(auto_now_add=True)
    recall_failures = models.FloatField(default=0.0)
    recall_successes = models.FloatField(default=0.0)
    alpha_prior = models.FloatField(default=1.0)
    beta_prior = models.FloatField(default=1.0)
    
    class Meta:
        unique_together = ['user', 'korean_word']
        ordering = ['-created_at']
    
    def get_durations(self):
        try:
            return json.loads(self.last_5_durations)
        except:
            return []
    
    def set_durations(self, durations):
        self.last_5_durations = json.dumps(durations)
    
    def add_hover_duration(self, duration):
        durations = self.get_durations()
        durations.insert(0, duration)
        if len(durations) > 5:
            durations.pop()
        self.set_durations(durations)
        self.hover_count += 1
        self.total_hover_time += duration
        self.save()
    
    def get_average_duration(self):
        if self.hover_count == 0:
            return 0.0
        return self.total_hover_time / self.hover_count
    
    def get_retention_rate(self):
        return self.retention_rate
    
    def get_pos_display(self):
        pos_descriptions = {
            'NNG': 'General Noun',
            'NNP': 'Proper Noun',
            'NNB': 'Bound Noun',
            'NP': 'Pronoun',
            'NR': 'Numeral',
            'VV': 'Verb',
            'VA': 'Adjective',
            'VX': 'Auxiliary Verb',
            'VCP': 'Copula',
            'VCN': 'Negative Copula',
            'MM': 'Determiner',
            'MAG': 'General Adverb',
            'MAJ': 'Conjunctive Adverb',
            'IC': 'Interjection',
            'JKS': 'Subject Particle',
            'JKC': 'Complement Particle',
            'JKG': 'Genitive Particle',
            'JKO': 'Object Particle',
            'JKB': 'Adverbial Particle',
            'JKV': 'Vocative Particle',
            'JKQ': 'Quotative Particle',
            'JX': 'Auxiliary Particle',
            'JC': 'Conjunctive Particle',
            'EP': 'Pre-final Ending',
            'EF': 'Final Ending',
            'EC': 'Conjunctive Ending',
            'ETN': 'Nominal Ending',
            'ETM': 'Adnominal Ending',
            'XPN': 'Prefix',
            'XSN': 'Noun Suffix',
            'XSV': 'Verb Suffix',
            'XSA': 'Adjective Suffix',
            'XR': 'Root',
            'SF': 'Sentence-final Punctuation',
            'SP': 'Separator',
            'SS': 'Symbol',
            'SE': 'Ellipsis',
            'SO': 'Opening Bracket',
            'SW': 'Closing Bracket',
            'SL': 'Foreign Word',
            'SH': 'Chinese Character',
            'SN': 'Number'
        }
        return pos_descriptions.get(self.pos, self.pos)
    
    def __str__(self):
        return f"{self.user.username}: {self.korean_word} ({self.pos}) -> {self.english_translation}"


