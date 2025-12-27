import { useRef, useState } from "react";

export function useRealtimeSTTMinimal({
  onText,
  language = "en",
  transcribeModel = "gpt-4o-mini-transcribe-2025-12-15",
  tokenUrl = "http://127.0.0.1:8000/realtime-token",
  realtimeModel = "gpt-4o-realtime-preview-latest",
  onFinal, // optional: (finalText) => {}
} = {}) {
  const pcRef = useRef(null);
  const streamRef = useRef(null);
  const dcRef = useRef(null);

  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");

  const itemIdRef = useRef(null);
  const textRef = useRef("");
  const committedRef = useRef("");
  async function start() {
    if (recording) return;

    const tokenRes = await fetch(tokenUrl);
    const token = (await tokenRes.text()).trim();
    if (!tokenRes.ok) throw new Error(`realtime-token failed: ${token}`);
    if (!token) throw new Error("empty realtime token");

    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    pcRef.current = pc;

    const dc = pc.createDataChannel("oai-events");
    dcRef.current = dc;

    dc.onopen = () => {
      dc.send(
        JSON.stringify({
          type: "session.update",
          session: {
            modalities: ["text"],
            input_audio_transcription: {
              model: transcribeModel,
              language,
              prompt: "Languages: English, Korean, Russian ONLY",
            },
            input_audio_noise_reduction: { type: "near_field" },
            turn_detection: {
              type: "server_vad",
              threshold: 0.5,
              prefix_padding_ms: 300,
              silence_duration_ms: 500,
              create_response: false,
            },
          },
        })
      );
    };

    dc.onmessage = (e) => {
      const msg = JSON.parse(e.data);
    
      if (msg.type === "error") {
        console.error("Realtime error:", msg);
        return;
      }
    
      if (msg.type === "conversation.item.input_audio_transcription.delta") {
        const itemId = msg.item_id;
        if (!itemId) return;
    
        if (itemIdRef.current !== itemId) {
          itemIdRef.current = itemId;
          textRef.current = "";
        }
    
        const d = msg.delta || "";
        const cur = textRef.current;
    
        // cumulative -> replace, incremental -> append
        textRef.current = d.startsWith(cur) ? d : (cur + d);
    
        const full = (committedRef.current ? committedRef.current + " " : "") + textRef.current;
        setTranscript(full);
        onText?.(full);
        return;
      }
    
      if (msg.type === "conversation.item.input_audio_transcription.completed") {
        const finalText = (msg.transcript || "").trim();
        if (!finalText) return;
    
        committedRef.current = (committedRef.current ? committedRef.current + " " : "") + finalText;
    
        itemIdRef.current = null;
        textRef.current = "";
    
        setTranscript(committedRef.current);
        onText?.(committedRef.current);
        onFinal?.(finalText);
      }
    };
    

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    stream.getTracks().forEach((t) => pc.addTrack(t, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const sdpRes = await fetch(
      `https://api.openai.com/v1/realtime?model=${encodeURIComponent(realtimeModel)}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/sdp",
        },
        body: offer.sdp,
      }
    );

    if (!sdpRes.ok) {
      const err = await sdpRes.text();
      throw new Error(`Realtime SDP failed: ${err}`);
    }

    const answerSDP = await sdpRes.text();
    await pc.setRemoteDescription({ type: "answer", sdp: answerSDP });

    setRecording(true);
  }

  function stop() {
    try {
      dcRef.current?.close();
    } catch {}
    try {
      pcRef.current?.close();
    } catch {}
    try {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    } catch {}

    dcRef.current = null;
    pcRef.current = null;
    streamRef.current = null;

    itemIdRef.current = null;
    textRef.current = "";
    setTranscript("");
    setRecording(false);
  }

  function clear() {
    itemIdRef.current = null;
    textRef.current = "";
    committedRef.current = "";
    setTranscript("");
  }
  

  return { start, stop, clear, recording, transcript };
}
