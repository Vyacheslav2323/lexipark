import math
from datetime import datetime, timedelta
from django.utils import timezone


def get_user_parameters(user):
    return {
        'alpha': 1.0,
        'beta': 10.0,
        'lambda_decay': 0.1
    }


def calculate_time_delta_seconds(previous_update):
    if previous_update is None:
        return 0.0
    now = timezone.now()
    delta = (now - previous_update).total_seconds()
    return max(0.0, delta)


def bayesian_recall_update(vocab_entry, had_lookup, user_parameters=None):
    if user_parameters is None:
        user_parameters = get_user_parameters(vocab_entry.user)
    
    alpha = vocab_entry.alpha_prior
    beta = vocab_entry.beta_prior
    lambda_decay = user_parameters['lambda_decay']
    
    success_count = vocab_entry.recall_successes + 1
    failure_count = vocab_entry.recall_failures + (2 if had_lookup else 0)
    
    delta_seconds = calculate_time_delta_seconds(vocab_entry.last_recall_update)
    
    time_decay = math.exp(-lambda_decay * (delta_seconds / 86400.0))
    
    recall_probability = (
        (alpha + success_count) / 
        (alpha + beta + success_count + failure_count)
    ) * time_decay
    
    return min(1.0, max(0.0, recall_probability))


def update_vocabulary_recall(vocab_entry, had_lookup):
    user_params = get_user_parameters(vocab_entry.user)
    new_recall = bayesian_recall_update(vocab_entry, had_lookup, user_params)
    
    vocab_entry.retention_rate = new_recall
    vocab_entry.recall_successes += 1
    vocab_entry.recall_failures += 2 if had_lookup else 0
    vocab_entry.last_recall_update = timezone.now()
    
    return vocab_entry


def batch_update_recalls(user, word_interactions):
    from vocab.models import Vocabulary
    
    updated_entries = []
    for korean_word, had_lookup in word_interactions:
        try:
            vocab_entry = Vocabulary.objects.get(user=user, korean_word=korean_word)
            updated_entry = update_vocabulary_recall(vocab_entry, had_lookup)
            updated_entries.append(updated_entry)
        except Vocabulary.DoesNotExist:
            continue
    
    Vocabulary.objects.bulk_update(
        updated_entries, 
        ['retention_rate', 'recall_successes', 'recall_failures', 'last_recall_update']
    )
    
    return len(updated_entries) 