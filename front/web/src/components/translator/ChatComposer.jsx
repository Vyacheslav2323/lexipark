// src/components/translator/ChatComposer.jsx
import MicButton from "./MicButton";

export default function ChatComposer({
  inputValue,
  setInputValue,
  onSubmit,
  recording,
  onMicClick,
}) {
  return (
    <div className="card-footer" style={{ display: "flex", gap: "8px" }}>
      <form onSubmit={onSubmit} style={{ display: "flex", gap: "8px", flex: 1 }}>
        <input
          className="form-control"
          placeholder="Type a message..."
          style={{ flex: 1 }}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <MicButton recording={recording} onClick={onMicClick} />
      </form>
    </div>
  );
}
