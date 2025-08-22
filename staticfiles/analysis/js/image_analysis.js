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
        if (imageInput) imageInput.addEventListener('change', (e) => this.handleImageUpload(e.target.files[0]));
        if (processBtn) processBtn.style.display = 'none';
    }
    
    setupDragAndDrop() {
        const fileContainer = document.getElementById('fileContainer');
        
        if (!fileContainer) return;
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
            const loadingSpinner = document.getElementById('loadingSpinner');
            
            if (ocrImage) ocrImage.src = e.target.result;
            if (imageContainer) imageContainer.style.display = 'inline-block';
            this.state.currentImage = file;
            
            this.clearResults();
            this.showNotification(`Image uploaded: ${file.name}`, 'info');
            if (loadingSpinner) loadingSpinner.style.display = 'inline-block';
            this.processImageWithOCR();
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
            const loadingSpinner = document.getElementById('loadingSpinner');
            const finishBtn = document.getElementById('finish-analysis-btn');
            if (loadingSpinner) loadingSpinner.style.display = 'inline-block';
            
            const formData = new FormData();
            formData.append('image', this.state.currentImage);
            formData.append('confidence', '0');
            
            const response = await fetch(window.ANALYSIS_URLS.imageAnalysis, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': window.CSRF_TOKEN }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.state.ocrResults = result.ocr_data;
                await this.displayResults(result.ocr_data);
                this.showNotification(`Analysis Complete!`, 'success');
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
            const loadingSpinner = document.getElementById('loadingSpinner');
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        }
    }
    
    async displayResults(ocrResult) {
        this.clearResults();
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

    gradientForColor(color) {
        if (!color) return '';
        const m = color.match(/^rgba?\(([^)]+)\)$/);
        if (!m) return color;
        const parts = m[1].split(',').map(s => s.trim());
        const [r, g, b] = parts;
        const a = parts[3] !== undefined ? parseFloat(parts[3]) : 1;
        const base = `rgba(${r}, ${g}, ${b}, ${isNaN(a) ? 1 : a})`;
        const transparent = `rgba(${r}, ${g}, ${b}, 0)`;
        return `linear-gradient(to bottom, ${transparent} 0%, ${transparent} 90%, ${base} 100%)`;
    }

    async displayImageWithText(ocrDataObj) {
        const imageContainer = document.getElementById('imageContainer');
        if (!imageContainer) return;
        if (window.getComputedStyle(imageContainer).position === 'static') {
            imageContainer.style.position = 'relative';
        }
        const ocrItems = Array.isArray(ocrDataObj)
            ? ocrDataObj
            : (Array.isArray(ocrDataObj?.ocr_data) ? ocrDataObj.ocr_data : []);
        if (!ocrItems.length) {
            this.showNotification('OCR data format error', 'error');
            return;
        }
        const fullText = ocrItems.map(item => item.text).join(' ');
        const spans = this.buildOcrSpans({ ocrItems });
        let cursor = 0;
        const imgEl = document.getElementById('ocrImage');
        const imgRect = imgEl.getBoundingClientRect();
        const contRect = imageContainer.getBoundingClientRect();
        const imgOffsetX = imgRect.left - contRect.left;
        const imgOffsetY = imgRect.top - contRect.top;
        const loader = document.createElement('div');
        loader.style.cssText = 'margin-top:8px;color:#6c757d;text-align:center;';
        let dots = 0; loader.textContent = 'Analyzing';
        const tick = setInterval(() => { dots = (dots + 1) % 4; loader.textContent = 'Analyzing' + '.'.repeat(dots); }, 400);
        imageContainer.appendChild(loader);
        // sentence streaming
        const parts = fullText.split(/([.!?…]|[。！？])/);
        const sentences = [];
        for (let i=0;i<parts.length;i+=2) { const s=(parts[i]||'').trim(); const p=parts[i+1]||''; if (s) sentences.push(s + p); }
        for (const sentence of sentences) {
            /* eslint-disable no-await-in-loop */
            const res = await fetch('/analysis/api/analyze-sentence', { method:'POST', headers:{ 'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest' }, body: JSON.stringify({ sentence }) }).then(r=>r.json()).catch(()=>null);
            if (!res || !res.success) continue;
            const tmp = document.createElement('div');
            tmp.innerHTML = res.html || '';
            const elements = Array.from(tmp.querySelectorAll('.interactive-word'));
            const tokens = elements.map(el => {
                const styleAttr = el.getAttribute('style') || '';
                const inlineColor = (styleAttr.match(/background-color:\s*([^;]+)/i) || [])[1] || '';
                const isKnown = inlineColor && inlineColor.toLowerCase() !== 'transparent';
                return {
                    surface: el.textContent || '',
                    base: el.getAttribute('data-original') || '',
                    pos: el.getAttribute('data-pos') || '',
                    grammar_info: el.getAttribute('data-grammar') || '',
                    translation: el.getAttribute('data-translation') || '',
                    in_vocab: isKnown,
                    color: inlineColor
                };
            });
            for (let index=0; index<tokens.length; index++) {
                const wordData = tokens[index];
                if (!wordData || !wordData.surface) continue;
                const range = this.findTokenRange({ text: fullText, token: wordData.surface, fromIndex: cursor });
                if (!range) continue;
                cursor = range.end;
                const span = this.findItemForRange({ spans, start: range.start, end: range.end });
                if (!span || !span.item || !span.item.boundingBox) continue;
                const box = this.computeBox({ span, start: range.start, end: range.end });
                const overlay = document.createElement('div');
                overlay.className = 'text-overlay interactive-word ocr-word';
                overlay.id = `ocr-word-${Date.now()}-${index}`;
                overlay.setAttribute('data-original', wordData.base || wordData.surface);
                overlay.setAttribute('data-translation', wordData.translation || '');
                overlay.setAttribute('data-pos', wordData.pos || '');
                overlay.setAttribute('data-grammar', wordData.grammar_info || '');
                if (wordData.in_vocab) {
                    overlay.classList.add('in-vocab');
                    overlay.style.background = this.gradientForColor(wordData.color);
                } else {
                    const subtle = 'rgba(212, 237, 218, 0.6)';
                    overlay.style.background = this.gradientForColor(subtle);
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
                overlay.style.pointerEvents = 'auto';
                overlay.style.cursor = 'pointer';
                overlay.style.zIndex = '1000';
                overlay.style.minWidth = '10px';
                overlay.style.minHeight = '10px';
                overlay.style.boxSizing = 'border-box';
                imageContainer.appendChild(overlay);
                if (window.bindWordElementEvents) window.bindWordElementEvents(overlay);
            }
        }
        clearInterval(tick);
        loader.remove();
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