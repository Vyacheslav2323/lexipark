export function trackSentenceHoverDuration(punctuation, duration) {
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

export function trackHoverDuration(koreanWord, duration) {
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