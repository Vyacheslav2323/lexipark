import { addRecallInteraction } from './recall.js';
import { saveToVocabulary } from './vocabulary.js';
import { state } from './state.js';
import { showNotification, showSentenceTranslation, hideSentenceTranslation } from './ui.js';
import { handleAnalyzeSubmit } from './analysis.js';

function trackSentenceHoverDuration(punctuation, duration) {
  fetch('/analysis/track-sentence-hover/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      punctuation: punctuation,
      duration: duration
    })
  })
    .then(response => response.json())
    .then(data => {
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
  fetch('/analysis/track-hover/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      korean_word: koreanWord,
      duration: duration
    })
  })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        console.error('Error tracking hover:', data.error);
      }
    })
    .catch(error => {
      console.error('Network error in hover tracking:', error);
    });
}

export function setupWordsEvents() {
  document.querySelectorAll('.interactive-word[data-original]').forEach(function(word) {
    const original = word.getAttribute('data-original');
    if (word.classList.contains('in-vocab') || word.style.backgroundColor) {
      state.displayedVocabWords.add(original);
    }
  });
  document.querySelectorAll('.interactive-word').forEach(function(word) {
    let hoverStartTime = null;
    const original = word.getAttribute('data-original');
    word.addEventListener('mouseenter', function() {
      hoverStartTime = Date.now();
    });
    word.addEventListener('mouseleave', function() {
      if (hoverStartTime) {
        const hoverDuration = Date.now() - hoverStartTime;
        trackHoverDuration(original, hoverDuration);
        state.hoveredWords.add(original);
        if (word.classList.contains('in-vocab') || word.style.backgroundColor) {
          const hadLookup = hoverDuration > 1000;
          addRecallInteraction(original, hadLookup);
        }
        hoverStartTime = null;
      }
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
  });
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
    let translation = null;
    
    punctuation.addEventListener('mouseenter', function() {
      hoverStartTime = Date.now();
      
      if (!translation) {
        const sentence = this.getAttribute('data-sentence');
        fetch('/analysis/translate-sentence/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({sentence: sentence})
        })
        .then(response => response.json())
        .then(data => {
          translation = data.translation;
          showSentenceTranslation(this, translation);
        })
        .catch(error => {
          console.error('Translation error:', error);
        });
      } else {
        showSentenceTranslation(this, translation);
      }
    });
    
    punctuation.addEventListener('mouseleave', function() {
      if (hoverStartTime) {
        const hoverDuration = Date.now() - hoverStartTime;
        trackSentenceHoverDuration(this.textContent, hoverDuration);
        hoverStartTime = null;
      }
      hideSentenceTranslation();
    });
  });
} 