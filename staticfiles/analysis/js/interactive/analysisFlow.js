import { showNotification } from './notifications.js';
import { state } from './state.js';

export function attachFinishAnalysisListener(button) {
  button.addEventListener('click', function(e) {
    e.preventDefault();
    handleFinishAnalysis();
  });
}

export function handleFinishAnalysis() {
  const finishBtn = document.getElementById('finish-analysis-btn');
  const spinner = document.getElementById('finish-spinner');
  const text = finishBtn.getAttribute('data-text');
  if (!text || !text.trim()) {
    showNotification('No text to finish analysis', 'error');
    return;
  }
  spinner.style.display = 'inline-block';
  finishBtn.disabled = true;
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
      spinner.style.display = 'none';
      finishBtn.disabled = false;
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