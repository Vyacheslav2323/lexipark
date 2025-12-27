import { useEffect, useState } from "react";
import FlashCard from "../components/memorize/FlashCard";

const N = 5;

export default function Memorize() {
  const [cards, setCards] = useState([]);
  const [side, setSide] = useState("front");
  const [failures, setFailures] = useState(0);
  const [remaining, setRemaining] = useState(N);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/memorize/get-cards", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    })
      .then(res => {
        console.log("STATUS:", res.status);
        return res.json();
      })
      .then(data => {
        if (!Array.isArray(data)) {
          console.error("Unexpected response:", data);
          setCards([]);
        } else {
          setCards(data.slice(0, N));
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("FETCH ERROR:", err);
        setLoading(false);
      });
  }, []);
  
  
  if (loading) {
    return <h2>Loading…</h2>;
  }
  
  if (cards.length === 0) {
    return <h2>No cards available</h2>;
  }
  
  if (cards.length === 0 || remaining <= 0) {
    return <h2>Session complete</h2>;
  }
  
  
  const card = cards[0];

  // 4 & 5) swipe handler
  function next(result) {
    if (result === "fail") {
      setFailures(f => f + 1);
  
      // rotate card to back
      setCards(cs => [...cs.slice(1), cs[0]]);
      setSide("front");
      return;
    }
  
    // SUCCESS
    fetch("http://127.0.0.1:8000/memorize/review", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
      body: JSON.stringify({
        vocab_id: card.vocab_id,
        success: true,
        failures
      })
    });
  
    setFailures(0);
    setRemaining(r => r - 1);
  
    // remove card permanently
    setCards(cs => cs.slice(1));
    setSide("front");
  }
  

  function advance() {
    setIdx(i => i + 1);
    setSide("front");
  }

  return (
    <div style={containerStyle}>
      <div>{remaining} / {N}</div>

      <FlashCard
        key={card.vocab_id}
        onPass={() => next("pass")}
        onFail={() => next("fail")}
        onTap={() => setSide(s => s === "front" ? "back" : "front")}
      >
        {side === "front"
          ? <h1>{card.base}</h1>
          : <p>{card.translation}</p>}
      </FlashCard>

      <div style={{ marginTop: 20 }}>
        <button onClick={() => next("fail")}>←</button>
        <button onClick={() => next("pass")}>→</button>
      </div>
    </div>
  );
}

const containerStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  height: "90vh",
  justifyContent: "center"
};
