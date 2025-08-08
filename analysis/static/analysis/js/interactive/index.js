import { setupWordsEvents, setupSentenceEvents } from './interactions.js';
import { setupAnalysis, handleFinishAnalysis } from './analysis.js';

document.addEventListener('DOMContentLoaded', function() {
  setupWordsEvents();
  setupSentenceEvents();
  setupAnalysis();
});

window.handleFinishAnalysis = handleFinishAnalysis; 