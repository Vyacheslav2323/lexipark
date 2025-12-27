// src/components/translator/ExplainPopover.jsx
export default function ExplainPopover({ selection, onClick }) {
    if (!selection) return null;
  
    return (
      <div
        style={{
          position: "fixed",
          top: selection.y,
          left: selection.x,
          transform: "translate(-50%, -100%)",
          background: "#222",
          color: "#fff",
          padding: "6px 10px",
          borderRadius: "6px",
          fontSize: "12px",
          cursor: "pointer",
          zIndex: 1000,
        }}
        onClick={onClick}
      >
        Explain
      </div>
    );
  }
  