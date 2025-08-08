import { decodeHTMLEntities } from './utils.js';

export function showSentenceTranslation(element, translation) {
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

export function hideSentenceTranslation() {
  const tooltips = document.querySelectorAll('[style*="position: absolute"][style*="z-index: 1001"]');
  tooltips.forEach(tooltip => {
    tooltip.remove();
  });
} 