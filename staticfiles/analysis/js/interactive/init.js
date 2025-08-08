import { setupWordsEvents, setupSentenceEvents } from './interactions.js';
import { setupNavigationGuard } from './navigationGuard.js';
import { setupFinishObserver } from './observer.js';

export function initInteractive() {
  document.addEventListener('DOMContentLoaded', function() {
    setupWordsEvents();
    setupSentenceEvents();
    setupNavigationGuard();
    setupFinishObserver();
  });
} 