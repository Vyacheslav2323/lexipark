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