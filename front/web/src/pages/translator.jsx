import { useState } from "react";
import { useChat } from "../hooks/useChat";
import { useExplainSelection } from "../hooks/useExplainSelection";
import ExplainPopover from "../components/translator/ExplainPopover";
import ChatComposer from "../components/translator/ChatComposer";
import ChatMessages from "../components/translator/ChatMessages";
import { useRealtimeSTTMinimal } from "../hooks/useRealtimeSTT";

export default function Translator() {
  const [inputValue, setInputValue] = useState("");

  const { start, stop, recording } = useRealtimeSTTMinimal({
    onText: (text) => setInputValue(text)
  });
  

  const {
    messages,
    addAssistantPlaceholder,
    updateAssistantStreaming,
    finalizeAssistantMessage,
    translateAndAppend
  } = useChat();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!inputValue.trim()) return;
  
    const text = inputValue;
    setInputValue("");
  
    await translateAndAppend(text);
  }
  

  function handleMicClick() {
    if (recording) stop();
    else {
      setInputValue("");
      start();
    }
  }

  const {
    selection,
    handleSelection,
    explain
  } = useExplainSelection({
    addAssistantPlaceholder,
    finalizeAssistantMessage
  });

  return (
    <div className="card" style={{ height: "85vh" }}>
      <ChatMessages messages={messages} onSelect={handleSelection} />
      <ChatComposer
        inputValue={inputValue}
        setInputValue={setInputValue}
        onSubmit={handleSubmit}
        recording={recording}
        onMicClick={handleMicClick}
      />
      <ExplainPopover selection={selection} onClick={explain} />
    </div>
  );
}
