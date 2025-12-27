// src/hooks/useChat.js
import { useEffect, useRef, useState, useCallback } from "react";
import { apiGet, apiPost } from "../services/api";

export function useChat() {
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);

  // hydrate-per-chatId (NOT boolean)
  const hydratedChatIdRef = useRef(null);

  useEffect(() => {
    const stored = localStorage.getItem("chat_id");
    if (stored) setChatId(stored);
  }, []);

  useEffect(() => {
    if (chatId) return;

    (async () => {
      try {
        const raw = await apiGet("/chat");
        const chats = Array.isArray(raw) ? raw : (raw?.chats ?? []);
        if (chats.length) {
          setChatId(chats[0].id ?? chats[0].chat_id);
        }
      } catch (e) {
        console.error("apiGet /chat failed:", e);
      }
    })();
  }, [chatId]);

  useEffect(() => {
    if (!chatId) return;
    if (hydratedChatIdRef.current === chatId) return;

    (async () => {
      try {
        const raw = await apiGet(`/chat/${chatId}`);
        const arr = Array.isArray(raw) ? raw : (raw?.messages ?? raw?.data ?? []);
        setMessages(arr.map(m => ({
          id: m.id ?? m.message_id ?? crypto.randomUUID(),
          role: m.role,
          text: m.text ?? m.content ?? ""
        })));
        hydratedChatIdRef.current = chatId; // set only after success
      } catch (e) {
        console.error(`apiGet /chat/${chatId} failed:`, e);
        hydratedChatIdRef.current = null; // allow retry
      }
    })();
  }, [chatId]);

  const ensureChat = useCallback(async () => {
    if (chatId) return chatId;
    const data = await apiPost("/chat/create", {});
    const id = data.chat_id ?? data.id ?? data?.chat?.id;
    setChatId(id);
    localStorage.setItem("chat_id", id);
    return id;
  }, [chatId]);

  const saveMessage = useCallback(async (cid, role, text) => {
    if (!cid) return;
    try {
      await apiPost("/chat/message", { chat_id: cid, role, text });
    } catch (e) {
      console.error("apiPost /chat/message failed:", e);
    }
  }, []);

  const addMessage = useCallback((msg) => {
    setMessages(m => [...m, msg]);
  }, []);

  const updateMessage = useCallback((id, patch) => {
    setMessages(m => m.map(x => (x.id === id ? { ...x, ...patch } : x)));
  }, []);

  return { chatId, setChatId, messages, setMessages, ensureChat, saveMessage, addMessage, updateMessage };
}
