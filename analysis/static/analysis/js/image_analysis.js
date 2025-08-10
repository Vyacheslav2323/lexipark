// Image Analysis JavaScript - Only handles OCR positioning, uses existing analysis tools
class ImageAnalysis {
    constructor() {
        this.state = {
            currentImage: null,
            ocrResults: null
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupDragAndDrop();
        console.log('Image Analysis initialized!');
    }
    
    bindEvents() {
        const imageInput = document.getElementById('imageInput');
        const processBtn = document.getElementById('processBtn');
        const finishBtn = document.getElementById('finishBtn');
        const confidenceSlider = document.getElementById('confidenceSlider');
        const confidenceValue = document.getElementById('confidenceValue');
        
        imageInput.addEventListener('change', (e) => this.handleImageUpload(e.target.files[0]));
        processBtn.addEventListener('click', () => this.processImageWithOCR());
        finishBtn.addEventListener('click', () => this.finishAnalysis());
        confidenceSlider.addEventListener('input', (e) => {
            confidenceValue.textContent = e.target.value;
        });
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
            imageContainer.style.display = 'block';
            processBtn.disabled = false;
            this.state.currentImage = file;
            
            this.clearResults();
            document.getElementById('finishBtn').disabled = true;
            
            this.showNotification(`Image uploaded: ${file.name}`, 'info');
        };
        reader.readAsDataURL(file);
    }
    
    async processImageWithOCR() {
        if (!this.state.currentImage) return;
        
        try {
            const processBtn = document.getElementById('processBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            
            processBtn.disabled = true;
            loadingSpinner.style.display = 'inline-block';
            processBtn.querySelector('span').textContent = 'Processing...';
            
            const formData = new FormData();
            formData.append('image', this.state.currentImage);
            formData.append('confidence', document.getElementById('confidenceSlider').value);
            
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
            console.log('OCR result:', result);
            
            if (result.success) {
                this.state.ocrResults = result.ocr_data.ocr_data; // Fix: access the nested ocr_data
                console.log('OCR result:', result.ocr_data);
                this.displayResults(result.ocr_data);
                document.getElementById('finishBtn').disabled = false;
                
                this.showNotification(`OCR completed! Found ${result.ocr_data.filtered_items} words.`, 'success');
            } else {
                throw new Error(result.error || 'OCR processing failed');
            }
            
        } catch (error) {
            console.error('OCR processing failed:', error);
            this.showNotification(`OCR processing failed: ${error.message}`, 'warning');
        } finally {
            const processBtn = document.getElementById('processBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            
            processBtn.disabled = false;
            loadingSpinner.style.display = 'none';
            processBtn.querySelector('span').textContent = 'Process Image';
        }
    }
    
    displayResults(ocrResult) {
        this.clearResults();
        
        // Display the image with text positioned correctly
        this.displayImageWithText(ocrResult.ocr_data); // Pass the ocr_data array
        
        // Display the extracted text for analysis
        this.displayExtractedText(ocrResult.ocr_data); // Pass the ocr_data array
        
        // Setup the existing analysis tools
        // The existing analysis tools will be used when the user clicks "Analyze This Text"
        // which will redirect to the page1 analysis page
        console.log('Image analysis ready - use "Analyze This Text" button to analyze extracted text');
    }
    
    displayImageWithText(ocrData) {
        const imageContainer = document.getElementById('imageContainer');
        const ocrImage = document.getElementById('ocrImage');
        
        // Position interactive word boxes on the image (no text content)
        ocrData.forEach(item => {
            const overlay = document.createElement('div');
            overlay.className = 'text-overlay interactive-word';
            
            // Set required data attributes for interactivity
            overlay.setAttribute('data-original', item.text);
            overlay.setAttribute('data-translation', item.text);
            overlay.setAttribute('data-pos', 'N/A');
            overlay.setAttribute('data-grammar', 'N/A');
            
            // Calculate position with bounds checking
            let left = item.boundingBox.x * 100;
            let top = item.boundingBox.y * 100;
            let width = item.boundingBox.w * 100;
            let height = item.boundingBox.h * 100;
            
            // Ensure overlay doesn't go too far outside image bounds
            if (left < -20) left = -20;
            if (top < -20) top = -20;
            if (left + width > 120) left = 120 - width;
            if (top + height > 120) top = 120 - height;
            
            // Position and size the overlay properly
            overlay.style.position = 'absolute';
            overlay.style.left = left + '%';
            overlay.style.top = top + '%';
            overlay.style.width = width + '%';
            overlay.style.height = height + '%';
            
            // Make it interactive
            overlay.style.pointerEvents = 'auto';
            overlay.style.cursor = 'pointer';
            
            imageContainer.appendChild(overlay);
        });
        
        // Let the existing interactive system handle all events
        // The interactive/index.js will automatically setup events for new .interactive-word elements
    }
    
    displayExtractedText(ocrData) {
        const wordInfo = document.getElementById('wordInfo');
        const wordList = document.getElementById('wordList');
        
        // Show the extracted text that can be analyzed
        const extractedText = ocrData.map(item => item.text).join(' ');
        wordList.innerHTML = `
            <p><strong>Extracted Text:</strong> ${extractedText}</p>
            <div class="mt-3">
                <button class="btn btn-primary" id="analyzeTextBtn">
                    <i class="fas fa-language me-2"></i>Analyze This Text
                </button>
            </div>
        `;
        wordInfo.style.display = 'block';
        
        // Add event listener for analyze button
        document.getElementById('analyzeTextBtn').addEventListener('click', () => {
            this.analyzeExtractedText(extractedText);
        });
    }
    
    analyzeExtractedText(text) {
        // Use the existing page1 analysis functionality
        const textInput = document.createElement('input');
        textInput.type = 'hidden';
        textInput.name = 'textinput';
        textInput.value = text;
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/analysis/page1/';
        form.appendChild(textInput);
        
        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = window.CSRF_TOKEN;
        form.appendChild(csrfInput);
        
        // Submit the form
        document.body.appendChild(form);
        form.submit();
    }
    
    clearResults() {
        // Remove text overlays
        const overlays = document.querySelectorAll('.text-overlay');
        overlays.forEach(overlay => overlay.remove());
        
        // Clear extracted text
        const wordList = document.getElementById('wordList');
        wordList.innerHTML = '';
        document.getElementById('wordInfo').style.display = 'none';
    }
    
    finishAnalysis() {
        this.showNotification('Analysis completed!', 'success');
        document.getElementById('finishBtn').disabled = true;
    }
    
    showNotification(message, type = 'info') {
        // Use the existing notification system from interactive/ui.js if available
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // Fallback simple notification
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
