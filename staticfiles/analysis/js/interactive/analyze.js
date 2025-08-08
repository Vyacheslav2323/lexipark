import { showNotification } from './notifications.js';

export function handleAnalyzeSubmit() {
  const btn = document.getElementById('analyze-btn');
  const spinner = document.getElementById('analyze-spinner');
  const textInput = document.getElementById('textinput');
  const text = textInput.value.trim();
  if (!text) {
    showNotification('Please enter text to analyze', 'error');
    return false;
  }
  spinner.style.display = 'inline-block';
  btn.disabled = true;
  return true;
} 