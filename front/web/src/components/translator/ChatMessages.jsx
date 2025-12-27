// src/components/translator/ChatMessages.jsx
export default function ChatMessages({ messages, onSelect }) {
    return (
      <div
        className="card-body"
        style={{ display: "flex", flexDirection: "column", gap: "8px", overflowY: "auto" }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`msg ${msg.role} ${msg.typing ? "typing" : ""}`}
            onMouseUp={() => onSelect(msg.text)}
          >
            {msg.text}
          </div>
        ))}
      </div>
    );
  }
  