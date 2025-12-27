import { useState, useRef, useEffect } from 'react';
import MicButton from '../components/translator/MicButton';
import { useRealtimeSTT } from '../hooks/useRealtimeSTT';

export default function Translator() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selection, setSelection] = useState(null);
  const msgIdRef = useRef(null);
  const [chatId, setChatId] = useState(null);
  const { recording, toggle } = useRealtimeSTT({
    onDelta: delta => {
      setMessages(m => m.map(msg => msg.id === msgIdRef.current ? { ...msg, text: msg.text + delta } : msg));
    },
    onComplete: () => {}
  });

  function handleMicClick() {
    if (recording) {
      toggle();
      return;
    }
    const id = crypto.randomUUID();
    msgIdRef.current = id;
    setMessages(m => [...m, { id, role: 'user', text: '' }]);
    toggle();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!inputValue.trim()) return;
    const text = inputValue;
    const id = crypto.randomUUID();
    setMessages(m => [...m, { id, role: 'user', text }]);
    setInputValue('');
    const cid = await ensureChat();
    saveMessage(cid, 'user', text);
    const token = localStorage.getItem("access_token");
    const translateResponse = await fetch('http://127.0.0.1:8000/llm/translate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ text })
    });
    const translateData = await translateResponse.json();
    const translateBotId = crypto.randomUUID();
    setMessages(m => [...m, { id: translateBotId, role: 'assistant', text: translateData.translation }]);
    saveMessage(cid, 'assistant', translateData.translation);
  }

  async function ensureChat() {
    if (chatId) return chatId;
    const token = localStorage.getItem("access_token");
    const res = await fetch('http://127.0.0.1:8000/chat/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      }
    });
    if (!res.ok) {
      throw new Error('Failed to create chat');
    }
    const data = await res.json();
    setChatId(data.chat_id);
    localStorage.setItem('chat_id', data.chat_id);
    return data.chat_id;
  }

  useEffect(() => {
    const storedChatId = localStorage.getItem('chat_id');
    if (storedChatId) setChatId(storedChatId);
  }, []);

  const hydratedRef = useRef(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    fetch("http://127.0.0.1:8000/chat", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(chats => {
        if (chats.length) {
          setChatId(chats[0].id);
        }
      });
  }, []);

  useEffect(() => {
    if (!chatId || hydratedRef.current) return;
    hydratedRef.current = true;
    const token = localStorage.getItem("access_token");
    fetch(`http://127.0.0.1:8000/chat/${chatId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setMessages(data.map(m => ({ id: m.id, role: m.role, text: m.text })));
      });
  }, [chatId]);

  async function saveMessage(chatId, role, text) {
    if (!chatId) {
      console.error('saveMessage called without chatId');
      return;
    }
    const token = localStorage.getItem("access_token");
    const res = await fetch('http://127.0.0.1:8000/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ chat_id: chatId, role, text })
    });
    if (!res.ok) {
      console.error('Failed to save message');
    }
  }

  async function handleExplain() {
    if (!selection) return;
    const { text, sentence } = selection;
    setSelection(null);
    const placeholderId = crypto.randomUUID();
    setMessages(m => [...m, { id: placeholderId, role: 'assistant', text: '', typing: true }]);
    const token = localStorage.getItem("access_token");
    const res = await fetch('http://127.0.0.1:8000/llm/lesson', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ grammar_vocab: text, sentence })
    });
    const data = await res.json();
    updateMessage(placeholderId, data.explanation ?? data.lesson ?? data.output ?? '');
    if (!chatId) return;
    saveMessage(chatId, 'assistant', data.explanation ?? data.lesson ?? data.output ?? '');
  }

  function handleSelection(e, sentence) {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (!text) {
      setSelection(null);
      return;
    }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    setSelection({ text, sentence, x: rect.left + rect.width / 2, y: rect.top - 8 });
  }

  function updateMessage(id, newText) {
    setMessages(m => m.map(msg => msg.id === id ? { ...msg, text: newText, typing: false } : msg));
  }

  return (
    <div className="card" style={{ height: '85vh' }}>
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`msg ${msg.role} ${msg.typing ? 'typing' : ''}`}
            onMouseUp={e => handleSelection(e, msg.text)}
          >
            {msg.text}
          </div>
        ))}
      </div>
      <div className="card-footer" style={{ display: 'flex', gap: '8px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', flex: 1 }}>
          <input
            className="form-control"
            placeholder="Type a message..."
            style={{ flex: 1 }}
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
          />
          <MicButton recording={recording} onClick={handleMicClick} />
        </form>
      </div>
      {selection && (
        <div
          style={{
            position: 'fixed',
            top: selection.y,
            left: selection.x,
            transform: 'translate(-50%, -100%)',
            background: '#222',
            color: '#fff',
            padding: '6px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            cursor: 'pointer',
            zIndex: 1000
          }}
          onClick={handleExplain}
        >
          Explain
        </div>
      )}
    </div>
  );
}
