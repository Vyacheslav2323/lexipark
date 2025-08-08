import { state } from './state.js';
import { finishAnalysis } from './analysisFlow.js';

export function setupNavigationGuard() {
  window.addEventListener('beforeunload', function(e) {
    if (state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      finishAnalysis();
      e.preventDefault();
      e.returnValue = 'Finish analysis?';
      return 'Finish analysis?';
    }
  });
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden' && state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      finishAnalysis();
    }
  });
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href && !link.href.startsWith('#') && state.displayedVocabWords.size > 0 && !state.isAnalysisFinished) {
      if (confirm('Finish analysis before leaving?')) {
        finishAnalysis();
      }
    }
  });
} 