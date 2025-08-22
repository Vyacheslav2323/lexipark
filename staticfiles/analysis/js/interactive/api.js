function notifyAuth() {
  if (window && window.showNotification) window.showNotification('Please login to continue', 'warning');
}

function sleep(ms) { return new Promise(res => setTimeout(res, ms)); }

async function postJson(u, d) {
  let tries = 0;
  let delay = 250;
  while (tries < 2) {
    try {
      const r = await fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify(d) });
      if (r.status === 401 || r.status === 403) { notifyAuth(); return null; }
      return await r.json();
    } catch (_) {
      await sleep(delay);
      delay *= 2;
      tries += 1;
    }
  }
  return { success: false, error: 'Network error' };
}

export function analyze(payload) {
  return postJson('/analysis/api/analyze', { text: payload.text || '' });
}

export function finish(payload) {
  return postJson('/analysis/api/finish', { text: payload.text || '' });
}

export function finishSentence(payload) {
  return postJson('/analysis/api/finish-sentence', { sentence: payload.sentence || '' });
}

export function finishBatch(payload) {
  return postJson('/analysis/api/finish-batch', { sentences: payload.sentences || [] });
}

export function batchRecall(payload) {
  return postJson('/analysis/api/batch-recall', { interactions: payload.interactions || [] });
}

export function translateWord(payload) {
  return postJson('/analysis/api/translate-word', { word: payload.word || '' });
}

export function translateSentence(payload) {
  return postJson('/analysis/api/translate-sentence', { sentence: payload.sentence || '' });
}

export function trackHover(payload) {
  return postJson('/analysis/track-hover/', { korean_word: payload.word || '', duration: payload.duration || 0 });
}

export function trackSentenceHover(payload) {
  return postJson('/analysis/track-sentence-hover/', { punctuation: payload.punctuation || '', duration: payload.duration || 0 });
}


