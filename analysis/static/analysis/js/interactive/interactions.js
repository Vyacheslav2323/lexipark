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

function setupPhotoImport() {
  const photoInput = document.getElementById('photo-input');
  const photoImportBtn = document.getElementById('photo-import-btn');
  const photoFilename = document.getElementById('photo-filename');
  const textInput = document.getElementById('textinput');
  
  if (photoImportBtn && photoInput) {
    photoImportBtn.addEventListener('click', function() {
      photoInput.click();
    });
    
    photoInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        const file = this.files[0];
        photoFilename.textContent = file.name;
        
        setPhotoImportLoading(true);
        
        processPhotoWithOCR(file)
          .then(extractedText => {
            if (textInput && extractedText) {
              textInput.value = extractedText;
              showNotification('Text extracted from photo successfully!', 'success');
            }
          })
          .catch(error => {
            console.error('OCR error:', error);
            console.error('Error details:', error.message);
            showNotification('Failed to extract text from photo: ' + error.message, 'error');
          })
          .finally(() => {
            setPhotoImportLoading(false);
          });
      }
    });
  }
}

export function setupWordsEvents() {
  setupPhotoImport();
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