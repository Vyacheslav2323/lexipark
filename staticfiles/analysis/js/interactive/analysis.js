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
  return true;
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
  fetch('/analysis/finish-analysis/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      text: text
    })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        showNotification(data.message, 'success');
        state.isAnalysisFinished = true;
        finishAnalysis();
        window.location.reload();
      } else {
        showNotification('Error finishing analysis: ' + data.error, 'error');
      }
    })
    .catch(error => {
      console.error('Network error in finish analysis:', error);
      showNotification('Network error while finishing analysis: ' + error.message, 'error');
    })
    .finally(() => {
      if (spinner) spinner.style.display = 'none';
      if (finishBtn) finishBtn.disabled = false;
    });
}

export function finishAnalysis() {
  if (state.isAnalysisFinished) return;
  const nonHoveredWords = Array.from(state.displayedVocabWords).filter(word => !state.hoveredWords.has(word));
  if (nonHoveredWords.length > 0) {
    const successInteractions = nonHoveredWords.map(word => [word, false]);
    state.recallInteractions.push(...successInteractions);
    fetch('/analysis/batch-update-recalls/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        interactions: successInteractions
      }),
      keepalive: true
    })
      .then(response => response.json())
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