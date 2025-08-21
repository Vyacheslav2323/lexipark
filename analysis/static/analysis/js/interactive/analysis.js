import { analyze as apiAnalyze, finish as apiFinish, batchRecall as apiBatchRecall } from './api.js'
import { showNotification } from './ui.js';
import { state } from './state.js';

export function handleAnalyzeSubmit() {
  const btn = document.getElementById('analyze-btn');
  const spinner = document.getElementById('analyze-spinner');
  const textInput = document.getElementById('textinput');
  const text = textInput ? textInput.value.trim() : '';
  if (!text) {
    showNotification('Please enter text to analyze', 'error');
    return false;
  }
  if (spinner) spinner.style.display = 'inline-block';
  if (btn) btn.disabled = true;
  startProgressiveAnalysis(text, {
    onFirstChunk: () => {
      if (spinner) spinner.style.display = 'none';
      if (btn) btn.disabled = false;
    },
    onComplete: () => {
      if (spinner) spinner.style.display = 'none';
      if (btn) btn.disabled = false;
    }
  });
  return false;
}

export function handleFinishAnalysis() {
  const finishBtn = document.getElementById('finish-analysis-btn');
  const spinner = document.getElementById('finish-spinner');
  const text = finishBtn ? finishBtn.getAttribute('data-text') : '';
  if (!text || !text.trim()) {
    showNotification('No text to finish analysis', 'error');
    return;
  }
  if (spinner) spinner.style.display = 'inline-block';
  if (finishBtn) finishBtn.disabled = true;
  const progressEl = (function(){
    const existing = document.getElementById('finish-progress');
    if (existing) return existing;
    const el = document.createElement('span');
    el.id = 'finish-progress';
    el.className = 'text-muted ms-2';
    if (finishBtn && finishBtn.parentNode) finishBtn.parentNode.appendChild(el);
    return el;
  })();
  const pairs = splitIntoSentences(text);
  const sentences = pairs.map(p => (p[0] || '').trim()).filter(Boolean);
  const chunkSize = 10;
  const chunks = [];
  for (let i=0;i<sentences.length;i+=chunkSize) chunks.push(sentences.slice(i,i+chunkSize));
  let done = 0;
  let totalAdded = 0;
  function updateProgress(){ if (progressEl) progressEl.textContent = `Saving ${Math.min(done*chunkSize, sentences.length)}/${sentences.length}…`; }
  function next(){
    if (done >= chunks.length) {
      showNotification(`Added ${totalAdded} words to vocabulary`, 'success');
      state.isAnalysisFinished = true;
      if (spinner) spinner.style.display = 'none';
      if (finishBtn) finishBtn.disabled = false;
      window.location.reload();
      return;
    }
    const chunk = chunks[done];
    fetch('/analysis/api/finish-batch', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ sentences: chunk }) })
      .then(r => r.json())
      .then(d => { totalAdded += (d && d.added_count) ? d.added_count : 0; })
      .catch(() => {})
      .finally(() => { done += 1; updateProgress(); next(); });
  }
  updateProgress();
  next();
}

export function finishAnalysis() {
  if (state.isAnalysisFinished) return;
  const nonHoveredWords = Array.from(state.displayedVocabWords).filter(word => !state.hoveredWords.has(word));
  if (nonHoveredWords.length > 0) {
    const successInteractions = nonHoveredWords.map(word => [word, false]);
    state.recallInteractions.push(...successInteractions);
    apiBatchRecall({ interactions: successInteractions })
      .then(data => {
        if (!data.success) {
          console.error('Error finishing analysis:', data.error);
        }
      })
      .catch(error => {
        console.error('Error finishing analysis:', error);
      });
  }
  state.isAnalysisFinished = true;
}

export function setupAnalysis() {
  window.addEventListener('beforeunload', function(e) {
    if (state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      finishAnalysis();
      e.preventDefault();
      e.returnValue = 'Finish analysis?';
      return 'Finish analysis?';
    }
  });
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden' && state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      finishAnalysis();
    }
  });
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href && !link.href.startsWith('#') && state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      if (confirm('Finish analysis before leaving?')) {
        finishAnalysis();
      }
    }
  });
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) {
            const finishBtn = node.querySelector ? node.querySelector('#finish-analysis-btn') : null;
            if (finishBtn) {
              finishBtn.addEventListener('click', function(e) {
                e.preventDefault();
                handleFinishAnalysis();
              });
            }
          }
        });
      }
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
  const existingFinishBtn = document.getElementById('finish-analysis-btn');
  if (existingFinishBtn) {
    existingFinishBtn.addEventListener('click', function(e) {
      e.preventDefault();
      handleFinishAnalysis();
    });
  }
  setTimeout(function() {
    const delayedFinishBtn = document.getElementById('finish-analysis-btn');
    if (delayedFinishBtn) {
      delayedFinishBtn.addEventListener('click', function(e) {
        e.preventDefault();
        handleFinishAnalysis();
      });
    }
  }, 1000);
} 

function splitIntoSentences(text) {
  const re = /([.!?…]|[。！？])/g;
  const out = [];
  let i = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    const s = text.slice(i, m.index);
    const p = m[0];
    out.push([s, p]);
    i = m.index + p.length;
  }
  if (i < text.length) out.push([text.slice(i), '']);
  return out;
}

function startProgressiveAnalysis(text, callbacks = {}) {
  const container = document.getElementById('analysis-result');
  if (container) container.innerHTML = '';
  const finishBtn = document.getElementById('finish-analysis-btn');
  if (finishBtn) finishBtn.setAttribute('data-text', text);
  if (finishBtn) finishBtn.classList.remove('d-none');
  if (finishBtn) finishBtn.style.display = 'block';
  const loader = document.createElement('div');
  loader.id = 'analysis-loading';
  loader.style.cssText = 'margin-top:12px;color:#6c757d;text-align:center;';
  let dots = 0;
  loader.textContent = 'Analyzing';
  const tick = setInterval(() => { dots = (dots + 1) % 4; loader.textContent = 'Analyzing' + '.'.repeat(dots); }, 400);
  container.appendChild(loader);
  const pairs = splitIntoSentences(text);
  if (pairs.length === 0) { clearInterval(tick); loader.remove(); if (callbacks.onComplete) callbacks.onComplete(); return; }
  let currentIndex = 0;
  let firstChunkSeen = false;
  let lastSentence = '';
  function processNext() {
    if (currentIndex >= pairs.length) { clearInterval(tick); loader.remove(); if (callbacks.onComplete) callbacks.onComplete(); return; }
    const [s, p] = pairs[currentIndex];
    if (!s.trim()) {
      if (s.length) { container.appendChild(document.createTextNode(s)); container.appendChild(loader); }
      if (p) { const ps = document.createElement('span'); ps.className='sentence-punctuation'; ps.style.position='relative'; ps.style.display='inline-block'; ps.style.cursor='default'; ps.setAttribute('data-sentence', lastSentence); ps.textContent=p; container.appendChild(ps); container.appendChild(loader); }
      currentIndex += 1; processNext(); return;
    }
    fetch('/analysis/api/analyze-sentence', { method:'POST', headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'}, body: JSON.stringify({ sentence: s }) })
      .then(r=>r.json())
      .then(d=>{
        if (d && d.success) {
          const span = document.createElement('span');
          span.style.cssText = 'font-size:18px;line-height:1.6;';
          span.innerHTML = d.html;
          container.appendChild(span);
          if (p) { const ps = document.createElement('span'); ps.className='sentence-punctuation'; ps.style.position='relative'; ps.style.display='inline-block'; ps.style.cursor='default'; ps.setAttribute('data-sentence', s); ps.textContent=p; container.appendChild(ps); }
          container.appendChild(loader);
          span.querySelectorAll('.interactive-word').forEach(w => { if (window.bindWordElementEvents) window.bindWordElementEvents(w); });
          if (window.setupSentenceEvents) window.setupSentenceEvents();
          if (window.queueSequentialTranslations) {
            const originals = Array.from(new Set(Array.from(span.querySelectorAll('.interactive-word[data-original]')).map(w => w.getAttribute('data-original'))));
            if (originals.length) window.queueSequentialTranslations(originals);
          }
          lastSentence = s;
          if (!firstChunkSeen && callbacks.onFirstChunk) { firstChunkSeen = true; callbacks.onFirstChunk(); }
        }
        currentIndex += 1; processNext();
      })
      .catch(()=>{ currentIndex += 1; processNext(); })
  }
  processNext();
}