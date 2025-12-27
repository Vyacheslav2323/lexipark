import { useEffect, useRef, useState, useCallback } from "react";
import { apiGet, apiPost } from "../services/api";

export function useChat() {
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const hydratedChatIdRef = useRef(null);

  // restore chat id
  useEffect(() => {
    const stored = localStorage.getItem("chat_id");
    if (stored) setChatId(stored);
  }, []);

  // fetch latest chat if none
  useEffect(() => {
    if (chatId) return;
    (async () => {
      const chats = await apiGet("/chat");
      if (chats?.length) setChatId(chats[0].id);
    })();
  }, [chatId]);

  // hydrate messages
  useEffect(() => {
    if (!chatId) return;
    if (hydratedChatIdRef.current === chatId) return;

    (async () => {
      const data = await apiGet(`/chat/${chatId}`);
      setMessages(
        data.map(m => ({
          id: m.id,
          role: m.role,
          text: m.text
        }))
      );
      hydratedChatIdRef.current = chatId;
    })();
  }, [chatId]);

  const ensureChat = useCallback(async () => {
    if (chatId) return chatId;
    const data = await apiPost("/chat/create", {});
    setChatId(data.chat_id);
    localStorage.setItem("chat_id", data.chat_id);
    return data.chat_id;
  }, [chatId]);

  const addUserMessage = useCallback(async (text) => {
    const id = crypto.randomUUID();
    setMessages(m => [...m, { id, role: "user", text }]);

    const cid = await ensureChat();
    await apiPost("/chat/message", { chat_id: cid, role: "user", text });
    return cid;
  }, [ensureChat]);

  const addAssistantPlaceholder = useCallback(() => {
    const id = crypto.randomUUID();
    setMessages(m => [...m, { id, role: "assistant", text: "", typing: true }]);
    return id;
  }, []);

  const updateAssistantStreaming = useCallback((id, delta) => {
    setMessages(m =>
      m.map(x =>
        x.id === id
          ? { ...x, text: (x.text ?? "") + delta }
          : x
      )
    );
  }, []);
  
  const finalizeAssistantMessage = useCallback(async (id, text, cidOverride) => {
    setMessages(m =>
      m.map(x => x.id === id ? { ...x, text, typing: false } : x)
    );
  
    const cid = cidOverride ?? chatId ?? await ensureChat(); // ✅ robust
    await apiPost("/chat/message", { chat_id: cid, role: "assistant", text });
  }, [chatId, ensureChat]);
  
  const translateAndAppend = useCallback(async (text) => {
    const cid = await addUserMessage(text);          // saves user msg
    const botId = addAssistantPlaceholder();         // typing bubble
  
    const data = await apiPost("/llm/translate", { text });
    const out = data.translation ?? data.output ?? "";
  
    await finalizeAssistantMessage(botId, out, cid); // update + persist assistant
    return out;
  }, [addUserMessage, addAssistantPlaceholder, finalizeAssistantMessage]);

  return {
    chatId,
    messages,
    addUserMessage,
    addAssistantPlaceholder,
    updateAssistantStreaming,
    finalizeAssistantMessage,
    translateAndAppend,
  };
  
}
