export function decodeHTMLEntities(text) {
  const textarea = document.createElement('textarea');
  textarea.innerHTML = text;
  return textarea.value;
}

export function showNotification(message, type) {
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
  return tooltip;
}

export function hideSentenceTranslation() {
  const tooltips = document.querySelectorAll('[style*="position: absolute"][style*="z-index: 1001"]');
  tooltips.forEach(tooltip => {
    tooltip.remove();
  });
} 