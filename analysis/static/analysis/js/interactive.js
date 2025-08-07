
let recallInteractions = [];
let recallBatchTimeout = null;
let hoveredWords = new Set();
let displayedVocabWords = new Set();
let isAnalysisFinished = false;

function getCookie(name) {
  let v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.interactive-word[data-original]').forEach(function(word) {
        const original = word.getAttribute('data-original');
        if (word.classList.contains('in-vocab') || word.style.backgroundColor) {
            displayedVocabWords.add(original);
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
                
                hoveredWords.add(original);
                
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
                hoveredWords.add(original);
                addRecallInteraction(original, true);
            } else {
                saveToVocabulary(original, pos, grammar, translation);
            }
        });
    });

    const analyzeForm = document.getElementById('analyze-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            if (!handleAnalyzeSubmit()) {
                e.preventDefault();
            }
        });
    }

    // We'll attach the event listener dynamically when the button appears
    
    window.addEventListener('beforeunload', function(e) {
        if (displayedVocabWords.size > 0 && !isAnalysisFinished) {
            finishAnalysis();
            e.preventDefault();
            e.returnValue = 'Finish analysis?';
            return 'Finish analysis?';
        }
    });
    
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden' && displayedVocabWords.size > 0 && !isAnalysisFinished) {
            finishAnalysis();
        }
    });
    
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('#') && displayedVocabWords.size > 0 && !isAnalysisFinished) {
            if (confirm('Finish analysis before leaving?')) {
                finishAnalysis();
            }
        }
    });

    document.querySelectorAll('.sentence-punctuation').forEach(function(punctuation) {
        let hoverStartTime = null;
        const sentenceTranslation = punctuation.getAttribute('data-sentence-translation');
        
        punctuation.addEventListener('mouseenter', function() {
            hoverStartTime = Date.now();
            showSentenceTranslation(this, sentenceTranslation);
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
    
    // Set up a mutation observer to watch for when the finish analysis button appears
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        const finishBtn = node.querySelector ? node.querySelector('#finish-analysis-btn') : null;
                        if (finishBtn) {
                            attachFinishAnalysisListener(finishBtn);
                        }
                    }
                });
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Also check if button already exists
    const existingFinishBtn = document.getElementById('finish-analysis-btn');
    if (existingFinishBtn) {
        attachFinishAnalysisListener(existingFinishBtn);
    }
    
    // Also try to attach the listener after a short delay
    setTimeout(function() {
        const delayedFinishBtn = document.getElementById('finish-analysis-btn');
        if (delayedFinishBtn) {
            attachFinishAnalysisListener(delayedFinishBtn);
        }
    }, 1000);
});

function attachFinishAnalysisListener(button) {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        handleFinishAnalysis();
    });
}

function handleAnalyzeSubmit() {
    const btn = document.getElementById('analyze-btn');
    const spinner = document.getElementById('analyze-spinner');
    const textInput = document.getElementById('textinput');
    const text = textInput.value.trim();

    if (!text) {
        showNotification('Please enter text to analyze', 'error');
        return false; // Prevent form submission
    }

    spinner.style.display = 'inline-block';
    btn.disabled = true;
    
    return true; // Allow form submission
}

function handleFinishAnalysis() {
    const finishBtn = document.getElementById('finish-analysis-btn');
    const spinner = document.getElementById('finish-spinner');
    const text = finishBtn.getAttribute('data-text');
    
    if (!text || !text.trim()) {
        showNotification('No text to finish analysis', 'error');
        return;
    }
    
    spinner.style.display = 'inline-block';
    finishBtn.disabled = true;
    
    // First, save unknown words as known (alpha=10, beta=0)
    fetch('/analysis/finish-analysis/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
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
            isAnalysisFinished = true;
            
            // Then update recall rates for non-hovered words
            finishAnalysis();
            
            // Refresh the page to show updated vocabulary
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

function showSentenceTranslation(element, translation) {
    const tooltip = document.createElement('div');
    tooltip.textContent = decodeHTMLEntities(translation);
    tooltip.style.cssText = `
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 14px;
        white-space: nowrap;
        z-index: 1001;
        min-width: 400px;
        max-width: 600px;
        word-wrap: break-word;
        white-space: normal;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        opacity: 0;
        transition: opacity 0.2s;
    `;
    
    element.style.position = 'relative';
    element.appendChild(tooltip);
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
}

function decodeHTMLEntities(text) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}

function hideSentenceTranslation() {
    const tooltips = document.querySelectorAll('[style*="position: absolute"][style*="z-index: 1001"]');
    tooltips.forEach(tooltip => {
        tooltip.remove();
    });
}

function trackSentenceHoverDuration(punctuation, duration) {
    fetch('/analysis/track-sentence-hover/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
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
            'X-Requested-With': 'XMLHttpRequest',
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

function addRecallInteraction(koreanWord, hadLookup) {
    recallInteractions.push([koreanWord, hadLookup]);
    
    if (recallBatchTimeout) {
        clearTimeout(recallBatchTimeout);
    }
    
    recallBatchTimeout = setTimeout(() => {
        sendBatchRecallUpdates();
    }, 1000);
}

function sendBatchRecallUpdates() {
    if (recallInteractions.length === 0) return;
    
    const interactions = [...recallInteractions];
    recallInteractions = [];
    
    fetch('/analysis/batch-update-recalls/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
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

function saveToVocabulary(koreanWord, pos, grammarInfo, translation) {
    const formData = new FormData();
    formData.append('korean_word', koreanWord);
    formData.append('pos', pos);
    formData.append('grammar_info', grammarInfo);
    formData.append('translation', translation);
    
    fetch('/users/save-vocabulary/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
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

function finishAnalysis() {
    if (isAnalysisFinished) return;
    
    const nonHoveredWords = Array.from(displayedVocabWords).filter(word => !hoveredWords.has(word));
    if (nonHoveredWords.length > 0) {
        const successInteractions = nonHoveredWords.map(word => [word, false]);
        recallInteractions.push(...successInteractions);
        
        fetch('/analysis/batch-update-recalls/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
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
    
    isAnalysisFinished = true;
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    let alertClass = 'alert-info';
    if (type === 'success') alertClass = 'alert-success';
    if (type === 'error') alertClass = 'alert-danger';
    if (type === 'info') alertClass = 'alert-info';
    
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
} 