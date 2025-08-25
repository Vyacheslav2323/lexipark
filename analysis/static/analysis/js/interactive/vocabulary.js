import { showNotification } from './ui.js';
import { translateWord as apiTranslateWord } from './api.js'

function requestTranslation(word) {
  return apiTranslateWord({ word }).then(d => d.success ? d.translation : '').catch(() => '');
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
          } else if (window.overlayGradientForColor) {
            document.querySelectorAll('.ocr-word.interactive-word[data-original="' + koreanWord + '"]').forEach(function(el){
              el.classList.add('in-vocab');
              el.style.background = window.overlayGradientForColor('rgba(238, 179, 196, 0.9)');
              el.style.backgroundColor = '';
            });
            document.querySelectorAll('.interactive-word:not(.ocr-word)[data-original="' + koreanWord + '"]').forEach(function(el) {
              el.classList.add('in-vocab');
              el.style.background = '';
              el.style.backgroundColor = 'rgba(238, 179, 196, 0.9)';
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