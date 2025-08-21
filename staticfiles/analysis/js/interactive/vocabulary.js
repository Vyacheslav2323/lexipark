import { showNotification } from './ui.js';

function requestTranslation(word) {
  return fetch('/analysis/translate-word/', {method:'POST', headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'}, body: JSON.stringify({word})})
    .then(r=>r.json())
    .then(d=> d.success ? d.translation : '')
    .catch(()=> '');
}

export function saveToVocabulary(koreanWord, pos, grammarInfo, translation) {
  const ensure = translation && translation.trim() ? Promise.resolve(translation) : requestTranslation(koreanWord);
  ensure.then(t => {
    const formData = new FormData();
    formData.append('korean_word', koreanWord);
    formData.append('pos', pos);
    formData.append('grammar_info', grammarInfo);
    formData.append('translation', t || koreanWord);
    fetch('/users/save-vocabulary/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showNotification('Word saved to vocabulary!', 'success');
          if (window.applyOcrOverlayColor && data.color) {
            window.applyOcrOverlayColor(koreanWord, data.color);
          } else {
            document.querySelectorAll('.interactive-word:not(.ocr-word)[data-original="' + koreanWord + '"]').forEach(function(el) {
              el.classList.add('in-vocab');
              el.style.backgroundColor = 'rgba(255, 255, 0, 0.9)';
            });
          }
        } else {
          console.error('Error saving vocabulary:', data.message);
          showNotification('Error saving word: ' + data.message, 'error');
        }
      })
      .catch(error => {
        console.error('Network error:', error);
        showNotification('Login to continue', 'error');
      });
  });
}