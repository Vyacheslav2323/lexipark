import { state } from './state.js';

export function addRecallInteraction(koreanWord, hadLookup) {
  state.recallInteractions.push([koreanWord, hadLookup]);
  if (state.recallBatchTimeout) {
    clearTimeout(state.recallBatchTimeout);
  }
  state.recallBatchTimeout = setTimeout(() => {
    sendBatchRecallUpdates();
  }, 1000);
}

export function sendBatchRecallUpdates() {
  if (state.recallInteractions.length === 0) return;
  const interactions = [...state.recallInteractions];
  state.recallInteractions.length = 0;
  fetch('/analysis/batch-update-recalls/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      interactions: interactions
    })
  })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        console.error('Error in batch recall update:', data.error);
      }
    })
    .catch(error => {
      console.error('Network error in batch recall update:', error);
    });
} 