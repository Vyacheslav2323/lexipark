import { attachFinishAnalysisListener } from './analysisFlow.js';

function attachIfExists() {
  const existingFinishBtn = document.getElementById('finish-analysis-btn');
  if (existingFinishBtn) {
    attachFinishAnalysisListener(existingFinishBtn);
  }
}

export function setupFinishObserver() {
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) {
            const finishBtn = node.querySelector ? node.querySelector('#finish-analysis-btn') : null;
            if (finishBtn) {
              attachFinishAnalysisListener(finishBtn);
            }
          }
        });
      }
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
  attachIfExists();
  setTimeout(function() {
    attachIfExists();
  }, 1000);
} 