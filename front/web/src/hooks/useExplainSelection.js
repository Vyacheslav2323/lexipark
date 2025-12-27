// src/hooks/useExplainSelection.js
import { useCallback, useState } from "react";
import { apiPost, apiGet } from "../services/api";

export function useExplainSelection({ updateMessage, chatId, saveMessage }) {
    const [selection, setSelection] = useState(null);
    const handleSelection = useCallback(async (sentence) => {
    const sel = window.getSelection();
    const text = sel?.toString()?.trim();

    if (!text) {
      setSelection(null);
      return;
    }

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

    const placeholderId = crypto.randomUUID();
    updateMessage(placeholderId, {}); // no-op if missing

    // add placeholder via caller (simpler: caller adds it)
    const data = await apiPost("/llm/lesson", { grammar_vocab: text, sentence });

    const out = data.explanation ?? data.lesson ?? data.output ?? "";
    updateMessage(placeholderId, { text: out, typing: false });

    if (chatId) saveMessage(chatId, "assistant", out);
  }, [selection, updateMessage, chatId, saveMessage]);

  return { selection, setSelection, handleSelection, explain };
}
