// src/hooks/useExplainSelection.js
import { useCallback, useState } from "react";
import { apiPost } from "../services/api";

export function useExplainSelection({ addAssistantPlaceholder, finalizeAssistantMessage }) {
  const [selection, setSelection] = useState(null);

  const handleSelection = useCallback((sentence) => {
    const sel = window.getSelection();
    const text = sel?.toString()?.trim();
    if (!text) return setSelection(null);

    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    setSelection({
      text,
      sentence,
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
    });
  }, []);

  const explain = useCallback(async () => {
    if (!selection) return;

    const { text, sentence } = selection;
    setSelection(null);

    const botId = addAssistantPlaceholder();

    const data = await apiPost("/llm/lesson", { grammar_vocab: text, sentence });
    const out = data.explanation ?? data.lesson ?? data.output ?? "";

    await finalizeAssistantMessage(botId, out);
  }, [selection, addAssistantPlaceholder, finalizeAssistantMessage]);

  return { selection, handleSelection, explain };
}
