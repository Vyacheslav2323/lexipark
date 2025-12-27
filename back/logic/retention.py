import numpy as np
from datetime import datetime

def update_recall(user_vocab, failures):
    now = datetime.utcnow()
    t_days = (now - (user_vocab.last_viewed or now)).total_seconds() / 86400
    a = user_vocab.learning_inertia or 0.8
    recall = np.exp(-(1 - a) * t_days)
    lambda_t = 2 ** (-t_days / 30)
    a = lambda_t * a + (1 - lambda_t) * (1 / (1 + failures))
    user_vocab.recall = float(recall)
    user_vocab.learning_inertia = float(a)
    user_vocab.last_viewed = now

def recompute_recall(user_vocab):
    if user_vocab.last_viewed is None:
        return
    now = datetime.utcnow()
    t_days = (now - (user_vocab.last_viewed or now)).total_seconds() / 86400
    a = user_vocab.learning_inertia or 0.8
    user_vocab.recall = float(np.exp(-(1 - a) * t_days))