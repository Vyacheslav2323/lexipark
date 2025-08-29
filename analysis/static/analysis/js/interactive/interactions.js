import { translateWord as apiTranslateWord, translateSentence as apiTranslateSentence, trackHover as apiTrackHover, trackSentenceHover as apiTrackSentenceHover } from './api.js'
import { addRecallInteraction } from './recall.js';
import { saveToVocabulary } from './vocabulary.js';
import { state } from './state.js';
function shouldTranslate(word, el) {
  if (!word) return false;
  if (!el) return true;
  const dt = el.getAttribute('data-translation');
  if (!dt) return true;
  if (dt === word) return true;
  return false;
}

function promoteTranslation(word) {
  if (!word) return;
  state.translationQueue = [word, ...state.translationQueue.filter(w => w !== word)];
  runTranslationQueue();
}

function ensureQueuedTranslation(original, el) {
  if (!shouldTranslate(original, el)) return;
  promoteTranslation(original);
}

function runTranslationQueue() {
  if (state.isTranslating) return;
  const next = state.translationQueue.shift();
  if (!next) return;
  state.isTranslating = true;
  apiTranslateWord({ word: next })
    .then(d=>{
      const t = d && d.success ? d.translation : '';
      document.querySelectorAll('.interactive-word[data-original="'+next+'"]').forEach(node=>{
        if (t && shouldTranslate(next, node)) node.setAttribute('data-translation', t);
        try{
          const tip = node.querySelector('.lp-tip');
          if (tip && t) tip.textContent = t;
        }catch(_){ }
      });
    })
    .catch(()=>{})
    .finally(()=>{
      state.isTranslating = false;
      runTranslationQueue();
    });
}

function queueSequentialTranslations(words) {
  words.forEach(w => ensureQueuedTranslation(w));
}
import { showNotification, showSentenceTranslation, hideSentenceTranslation } from './ui.js';
import { handleAnalyzeSubmit } from './analysis.js';

function trackSentenceHoverDuration(punctuation, duration) {
  apiTrackSentenceHover({ punctuation, duration })
    .then(data => {
      if (!data) return;
      if (data.success) {
        console.log('Sentence hover tracked:', data.message);
      } else {
        console.error('Error tracking sentence hover:', data.error);
      }
    })
    .catch(error => {
      console.error('Network error in sentence hover tracking:', error);
    });
}

function trackHoverDuration(koreanWord, duration) {
  apiTrackHover({ word: koreanWord, duration })
    .then(data => {
      if (!data) return;
      if (!data.success) {
        console.error('Error tracking hover:', data.error);
      }
    })
    .catch(error => {
      console.error('Network error in hover tracking:', error);
    });
}

export function bindWordElementEvents(word) {
  let hoverStartTime = null;
  const original = word.getAttribute('data-original');
  try{
    if (!word.querySelector('.lp-tip-link')){
      const link = document.createElement('a');
      link.className = 'lp-tip-link';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.style.display = 'none';
      word.appendChild(link);
    }
  }catch(_){ }
  word.addEventListener('mouseenter', function() {
    hoverStartTime = Date.now();
    ensureQueuedTranslation(original, word);
    try{
      const q = encodeURIComponent(original || '');
      const tipLink = word.querySelector('.lp-tip-link');
      if (tipLink){
        tipLink.href = 'https://papago.naver.com/?sk=ko&tk=en&hn=0&st=' + q;
        tipLink.textContent = word.getAttribute('data-translation') || original || '';
        tipLink.style.display = 'inline-block';
      }
    }catch(_){ }
  });
  word.addEventListener('mouseleave', function() {
    if (hoverStartTime) {
      const hoverDuration = Date.now() - hoverStartTime;
      trackHoverDuration(original, hoverDuration);
      state.hoveredWords.add(original);
      if (word.classList.contains('in-vocab') || word.style.backgroundColor) {
        if (hoverDuration >= 500) {
          const hadLookup = true;
          addRecallInteraction(original, hadLookup);
        }
      }
      hoverStartTime = null;
    }
    try{ const tipLink = word.querySelector('.lp-tip-link'); if (tipLink) tipLink.style.display = 'none'; }catch(_){ }
  });
  word.addEventListener('click', function() {
    const translation = this.getAttribute('data-translation');
    const pos = this.getAttribute('data-pos');
    const grammar = this.getAttribute('data-grammar');
    const isInVocab = this.classList.contains('in-vocab');
    if (isInVocab) {
      showNotification('Word is already in your vocabulary!', 'info');
      state.hoveredWords.add(original);
      addRecallInteraction(original, true);
    } else {
      saveToVocabulary(original, pos, grammar, translation);
    }
  });
}

function processPhotoWithOCR(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  return fetch('/analysis/process-photo-analysis/', {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken
    },
    body: formData
  })
  .then(response => {
    if (response.status === 401 || response.status === 403) {
      showNotification('Please login to continue', 'warning');
      throw new Error('Auth required');
    }
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      return response.text().then(text => {
        console.error('Non-JSON response:', text.substring(0, 200));
        throw new Error('Server returned non-JSON response. Check if you are logged in.');
      });
    }
    
    return response.json();
  })
  .then(data => {
    if (data.success) {
      return data.text;
    } else {
      throw new Error(data.error || 'OCR processing failed');
    }
  });
}

function setPhotoImportLoading(isLoading) {
  const photoImportBtn = document.getElementById('photo-import-btn');
  const photoFilename = document.getElementById('photo-filename');
  
  if (photoImportBtn) {
    photoImportBtn.disabled = isLoading;
    if (isLoading) {
      photoImportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    } else {
      photoImportBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Choose Photo';
    }
  }
  
  if (photoFilename) {
    if (isLoading) {
      photoFilename.textContent = 'Processing image...';
    }
  }
}

function setupPhotoImport() {}

export function setupWordsEvents() {
  setupPhotoImport();
  
  // Expose functions to window for use by other modules
  window.trackHoverDuration = trackHoverDuration;
  window.saveToVocabulary = saveToVocabulary;
  window.addRecallInteraction = addRecallInteraction;
  window.showNotification = showNotification;
  window.bindWordElementEvents = bindWordElementEvents;
  window.queueSequentialTranslations = queueSequentialTranslations;
  
  document.querySelectorAll('.interactive-word[data-original]').forEach(function(word) {
    const original = word.getAttribute('data-original');
    if (word.classList.contains('in-vocab') || word.style.backgroundColor) {
      state.displayedVocabWords.add(original);
    }
  });
  document.querySelectorAll('.interactive-word').forEach(function(word) {
    bindWordElementEvents(word);
  });
  const originals = Array.from(new Set(Array.from(document.querySelectorAll('.interactive-word[data-original]')).map(w => w.getAttribute('data-original'))));
  if (originals.length > 0) queueSequentialTranslations(originals);
  const analyzeForm = document.getElementById('analyze-form');
  if (analyzeForm) {
    analyzeForm.addEventListener('submit', function(e) {
      if (!handleAnalyzeSubmit()) {
        e.preventDefault();
      }
    });
  }
}

// ------------------------------

export function setupSentenceEvents() {
  document.querySelectorAll('.sentence-punctuation').forEach(function(punctuation) {
    let hoverStartTime = null;
    let currentTooltip = null;
    
    punctuation.addEventListener('mouseenter', function() {
      hoverStartTime = Date.now();
      
      const sentence = this.getAttribute('data-sentence') || '';
      apiTranslateSentence({ sentence })
        .then(data => {
          const translation = data && data.translation ? data.translation : '';
          currentTooltip = showSentenceTranslation(this, translation || sentence);
        })
        .catch(() => {})
    });
    
    punctuation.addEventListener('mouseleave', function() {
      if (hoverStartTime) {
        const hoverDuration = Date.now() - hoverStartTime;
        trackSentenceHoverDuration(this.textContent, hoverDuration);
        hoverStartTime = null;
      }
      hideSentenceTranslation();
      if (currentTooltip && currentTooltip.remove) { currentTooltip.remove(); currentTooltip = null; }
    });
  });
} 