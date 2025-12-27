import { useEffect, useState } from "react";
import VocabTable from "../components/mypage/VocabTable";
import GrammarTable from "../components/mypage/GrammarTable";
import { getToken } from "../services/auth";

const API_BASE = "http://127.0.0.1:8000";

async function apiGet(path) {
  const token = getToken();
  const r = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${text}`);
  }
  return r.json();
}

export default function Mypage() {
  const [vocab, setVocab] = useState([]);
  const [grammar, setGrammar] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const [v, g] = await Promise.all([
          apiGet("/mypage/vocab-table"),
          apiGet("/mypage/grammar-table"),
        ]);
        if (cancelled) return;
        setVocab(v);
        setGrammar(g);
      } catch (e) {
        if (cancelled) return;
        console.error(e);
        setErr(String(e?.message || e));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h2>My Learning Stats</h2>

      {err && (
        <div className="alert alert-danger" role="alert">
          {err}
        </div>
      )}

      <VocabTable data={vocab} />
      <GrammarTable data={grammar} />
    </div>
  );
}
