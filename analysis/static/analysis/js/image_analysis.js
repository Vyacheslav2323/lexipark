// Image Analysis JavaScript - Only handles OCR positioning, uses existing analysis tools
class ImageAnalysis {
    constructor() {
        this.state = {
            currentImage: null,
            ocrResults: null
        };
        
        this.init();

        window.applyOcrOverlayColor = (original, color) => {
            const gradient = this.gradientForColor(color);
            document.querySelectorAll('.ocr-word.interactive-word[data-original="' + original + '"]').forEach(el => {
                el.classList.add('in-vocab');
                el.style.background = gradient;
                el.style.backgroundColor = '';
            });
            document.querySelectorAll('.interactive-word:not(.ocr-word)[data-original="' + original + '"]').forEach(el => {
                el.classList.add('in-vocab');
                el.style.background = '';
                el.style.backgroundColor = 'rgba(255, 255, 0, 0.9)';
            });
        };
    }
    
    init() {
        this.bindEvents();
        this.setupDragAndDrop();
    }
    
    bindEvents() {
        const imageInput = document.getElementById('imageInput');
        const processBtn = document.getElementById('processBtn');
        
        imageInput.addEventListener('change', (e) => this.handleImageUpload(e.target.files[0]));
        processBtn.addEventListener('click', () => this.processImageWithOCR());
    }
    
    setupDragAndDrop() {
        const fileContainer = document.getElementById('fileContainer');
        
        fileContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileContainer.classList.add('drag-over');
        });
        
        fileContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileContainer.classList.remove('drag-over');
        });
        
        fileContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            fileContainer.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleImageUpload(files[0]);
            }
        });
    }
    
    handleImageUpload(file) {
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const ocrImage = document.getElementById('ocrImage');
            const imageContainer = document.getElementById('imageContainer');
            const processBtn = document.getElementById('processBtn');
            
            ocrImage.src = e.target.result;
            imageContainer.style.display = 'inline-block';
            processBtn.disabled = false;
            this.state.currentImage = file;
            
            this.clearResults();
            
            this.showNotification(`Image uploaded: ${file.name}`, 'info');
            
            ocrImage.onload = () => {
            };
        };
        reader.readAsDataURL(file);
    }
    
    async processImageWithOCR() {
        if (!this.state.currentImage) return;
        if (window.IS_AUTHENTICATED === false) {
            this.showNotification('Please login to continue', 'warning');
            return;
        }
        
        try {
            const processBtn = document.getElementById('processBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            const finishBtn = document.getElementById('finish-analysis-btn');
            
            processBtn.disabled = true;
            loadingSpinner.style.display = 'inline-block';
            processBtn.querySelector('span').textContent = 'Processing...';
            
            const formData = new FormData();
            formData.append('image', this.state.currentImage);
            formData.append('confidence', '0');
            
            const response = await fetch(window.ANALYSIS_URLS.imageAnalysis, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.state.ocrResults = result.ocr_data;
                
                // Keep loading state active during text analysis
                await this.displayResults(result.ocr_data);
                
                // Only stop loading after everything is complete
                this.showNotification(`Analysis Complete! Found ${result.ocr_data.filtered_items} text regions.`, 'success');
                if (finishBtn) {
                    const extractedText = (Array.isArray(result.ocr_data) ? result.ocr_data : (result.ocr_data?.ocr_data || [])).map(item => item.text).join(' ');
                    finishBtn.style.display = 'block';
                    finishBtn.setAttribute('data-text', extractedText);
                    if (!finishBtn._bound) {
                        finishBtn.addEventListener('click', (e) => {
                            e.preventDefault();
                            if (window.handleFinishAnalysis) window.handleFinishAnalysis();
                        });
                        finishBtn._bound = true;
                    }
                }
            } else {
                throw new Error(result.error || 'OCR processing failed');
            }
            
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showNotification(`Analysis failed: ${error.message}`, 'warning');
        } finally {
            const processBtn = document.getElementById('processBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            
            processBtn.disabled = false;
            loadingSpinner.style.display = 'none';
            processBtn.querySelector('span').textContent = 'Process Image';
        }
    }
    
    async displayResults(ocrResult) {
        this.clearResults();
        
        // Display the image with interactive text overlays
        await this.displayImageWithText(ocrResult);
    }
    
    buildOcrSpans(args) {
        const ocrItems = args.ocrItems || [];
        let offset = 0;
        const spans = [];
        for (const item of ocrItems) {
            const text = item.text || '';
            const start = offset;
            const end = start + text.length;
            spans.push({ item, start, end, text });
            offset = end + 1;
        }
        return spans;
    }

    findTokenRange(args) {
        const text = args.text || '';
        const token = args.token || '';
        const fromIndex = args.fromIndex || 0;
        const start = text.indexOf(token, fromIndex);
        if (start === -1) return null;
        return { start, end: start + token.length };
    }

    findItemForRange(args) {
        const spans = args.spans || [];
        const start = args.start;
        const end = args.end;
        for (const span of spans) {
            if (start >= span.start && end <= span.end) return span;
        }
        return null;
    }

    computeBox(args) {
        const span = args.span;
        const start = args.start;
        const end = args.end;
        const box = span.item.boundingBox;
        const widthChars = span.end - span.start || 1;
        const relStart = (start - span.start) / widthChars;
        const relEnd = (end - span.start) / widthChars;
        const left = (box.x + box.w * relStart) * 100;
        const top = box.y * 100;
        const width = (box.w * (relEnd - relStart)) * 100;
        const height = box.h * 100;
        return { left, top, width, height };
    }

    isInteractivePos(pos) {
        if (!pos) return false;
        if (['NNG','NNP','NP','NR','MAG','MAJ','MM'].includes(pos)) return true;
        if (pos.includes('VV') || pos.includes('VA') || pos.includes('VX')) return true;
        return false;
    }

    gradientForColor(color) {
        if (!color) return '';
        const m = color.match(/^rgba?\(([^)]+)\)$/);
        if (!m) return color;
        const parts = m[1].split(',').map(s => s.trim());
        const [r, g, b] = parts;
        const a = parts[3] !== undefined ? parseFloat(parts[3]) : 1;
        const base = `rgba(${r}, ${g}, ${b}, ${isNaN(a) ? 1 : a})`;
        const transparent = `rgba(${r}, ${g}, ${b}, 0)`;
        return `linear-gradient(to bottom, ${transparent} 0%, ${transparent} 85%, ${base} 100%)`;
    }

    async displayImageWithText(ocrDataObj) {
        const imageContainer = document.getElementById('imageContainer');
        const self = this; // Capture the ImageAnalysis instance
        
        // Make sure overlays position relative to the container
        if (window.getComputedStyle(imageContainer).position === 'static') {
            imageContainer.style.position = 'relative';
        }
        
        // Normalize items
        const ocrItems = Array.isArray(ocrDataObj)
            ? ocrDataObj
            : (Array.isArray(ocrDataObj?.ocr_data) ? ocrDataObj.ocr_data : []);
        
        if (!ocrItems.length) {
            this.showNotification('OCR data format error', 'error');
            return;
        }
        
        const extractedText = ocrItems.map(item => item.text).join(' ');
        
        return new Promise((resolve, reject) => {
            fetch('/analysis/analyze-ocr-text/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': window.CSRF_TOKEN
            },
            body: JSON.stringify({ text: extractedText })
        })
        .then(response => response.json())
        .then(analysisData => {
            if (analysisData.success) {
                const spans = this.buildOcrSpans({ ocrItems });
                let cursor = 0;
                const fullText = extractedText;
                const imgEl = document.getElementById('ocrImage');
                const imgRect = imgEl.getBoundingClientRect();
                const contRect = imageContainer.getBoundingClientRect();
                const imgOffsetX = imgRect.left - contRect.left;
                const imgOffsetY = imgRect.top - contRect.top;
                analysisData.words.forEach((wordData, index) => {
                    if (!wordData || !wordData.surface) return;
                    const base = wordData.base || wordData.surface;
                    if (!base) return;
                    if (!this.isInteractivePos(wordData.pos)) return;
                    const range = this.findTokenRange({ text: fullText, token: wordData.surface, fromIndex: cursor });
                    if (!range) return;
                    cursor = range.end;
                    const span = this.findItemForRange({ spans, start: range.start, end: range.end });
                    if (!span || !span.item || !span.item.boundingBox) return;
                    const box = this.computeBox({ span, start: range.start, end: range.end });
                    const overlay = document.createElement('div');
                    overlay.className = 'text-overlay interactive-word ocr-word';
                    overlay.id = `ocr-word-${index}`;
                    overlay.setAttribute('data-original', base);
                    overlay.setAttribute('data-translation', wordData.translation || (wordData.in_vocab ? (wordData.surface || '') : ''));
                    overlay.setAttribute('data-pos', wordData.pos || 'N/A');
                    overlay.setAttribute('data-grammar', wordData.grammar_info || 'N/A');
                    if (wordData.in_vocab) {
                        overlay.classList.add('in-vocab');
                        if (wordData.color) {
                            overlay.style.background = this.gradientForColor(wordData.color);
                        }
                    }
                    if (!wordData.in_vocab) {
                        const green = 'rgba(212, 237, 218, 1)';
                        overlay.style.background = this.gradientForColor(green);
                    }
                    overlay.style.position = 'absolute';
                    const leftPx = imgOffsetX + (box.left / 100) * imgRect.width;
                    const topPx = imgOffsetY + (box.top / 100) * imgRect.height;
                    const widthPx = (box.width / 100) * imgRect.width;
                    const heightPx = (box.height / 100) * imgRect.height;
                    overlay.style.left = leftPx + 'px';
                    overlay.style.top = topPx + 'px';
                    overlay.style.width = widthPx + 'px';
                    overlay.style.height = heightPx + 'px';
                    overlay.style.border = 'none';
                    // backgroundColor comes from CSS for unknowns and inline for known words
                    overlay.style.pointerEvents = 'auto';
                    overlay.style.cursor = 'pointer';
                    overlay.style.zIndex = '1000';
                    overlay.style.minWidth = '10px';
                    overlay.style.minHeight = '10px';
                    overlay.style.boxSizing = 'border-box';
                    imageContainer.appendChild(overlay);
                    if (window.bindWordElementEvents) window.bindWordElementEvents(overlay);
                });
                
                const finalCount = imageContainer.querySelectorAll('.text-overlay').length;
                resolve();
            } else {
                reject(new Error('Text analysis failed'));
            }
        })
        .catch(error => {
            reject(error);
        });
        });
    }
    
    clearResults() {
        const overlays = document.querySelectorAll('.text-overlay');
        overlays.forEach(overlay => overlay.remove());
    }
    
    showNotification(message, type = 'info') {
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ImageAnalysis();
});