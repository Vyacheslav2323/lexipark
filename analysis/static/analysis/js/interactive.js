console.log('Interactive.js loaded successfully');

let recallInteractions = [];
let recallBatchTimeout = null;
let hoveredWords = new Set();
let displayedVocabWords = new Set();
let isAnalysisFinished = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up interactive words');
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
            console.log(`Hover started on: ${original}`);
        });
        
        word.addEventListener('mouseleave', function() {
            if (hoverStartTime) {
                const hoverDuration = Date.now() - hoverStartTime;
                console.log(`Hover ended on: ${original}, duration: ${hoverDuration}ms`);
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
            
            console.log('Clicked:', original, '->', translation);
            console.log('POS:', pos);
            console.log('Grammar:', grammar);
            console.log('Already in vocab:', isInVocab);
            
            if (isInVocab) {
                showNotification('Word is already in your vocabulary!', 'info');
                hoveredWords.add(original);
                addRecallInteraction(original, true);
            } else {
                saveToVocabulary(original, pos, grammar, translation);
            }
        });
    });

    const finishAnalysisForm = document.getElementById('finish-analysis-form');
    if (finishAnalysisForm) {
        finishAnalysisForm.addEventListener('submit', function(e) {
            finishAnalysis();
        });
    }
    
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
            console.log(`Sentence hover started on punctuation: ${this.textContent}`);
            showSentenceTranslation(this, sentenceTranslation);
        });
        
        punctuation.addEventListener('mouseleave', function() {
            if (hoverStartTime) {
                const hoverDuration = Date.now() - hoverStartTime;
                console.log(`Sentence hover ended on punctuation: ${this.textContent}, duration: ${hoverDuration}ms`);
                trackSentenceHoverDuration(this.textContent, hoverDuration);
                hoverStartTime = null;
            }
            hideSentenceTranslation();
        });
    });
});

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
            console.log('Sentence hover tracked:', data);
        } else {
            console.error('Error tracking sentence hover:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error tracking sentence hover:', error);
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
        if (data.success) {
            if (data.message) {
                console.log('Hover tracked (word not in vocab):', data.message);
            } else {
                console.log('Hover tracked:', data);
            }
        } else {
            console.error('Error tracking hover:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error tracking hover:', error);
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
            console.log('Vocabulary saved:', data.message);
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
        showNotification('Network error while saving word', 'error');
    });
}

function addRecallInteraction(koreanWord, hadLookup) {
    recallInteractions.push([koreanWord, hadLookup]);
    
    if (recallBatchTimeout) {
        clearTimeout(recallBatchTimeout);
    }
    
    recallBatchTimeout = setTimeout(sendBatchRecallUpdates, 2000);
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
        if (data.success) {
            console.log(`Batch updated ${data.updated_count} recall rates`);
        } else {
            console.error('Error in batch recall update:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error in batch recall update:', error);
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
            if (data.success) {
                console.log(`Finished analysis: recorded ${nonHoveredWords.length} successful recalls for non-hovered words:`, nonHoveredWords);
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