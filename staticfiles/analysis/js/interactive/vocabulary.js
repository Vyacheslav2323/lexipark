import { showNotification } from './ui.js';

export function saveToVocabulary(koreanWord, pos, grammarInfo, translation) {
  const formData = new FormData();
  formData.append('korean_word', koreanWord);
  formData.append('pos', pos);
  formData.append('grammar_info', grammarInfo);
  formData.append('translation', translation);
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
        document.querySelectorAll('.interactive-word[data-original="' + koreanWord + '"]').forEach(function(el) {
          el.classList.add('in-vocab');
          el.style.backgroundColor = 'rgba(255, 255, 0, 0.9)';
        });
      } else {
        console.error('Error saving vocabulary:', data.message);
        showNotification('Error saving word: ' + data.message, 'error');
      }
    })
    .catch(error => {
      console.error('Network error:', error);
      showNotification('Login to continue', 'error');
    });
} 