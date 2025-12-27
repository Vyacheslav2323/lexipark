import { useRef, useState } from 'react';

export function useRealtimeSTT({ onDelta, onComplete }) {
  const [recording, setRecording] = useState(false);
  const pcRef = useRef(null);
  const streamRef = useRef(null);

  async function toggle() {
    if (recording) {
      pcRef.current?.close();
      streamRef.current?.getTracks().forEach(t => t.stop());
      setRecording(false);
      return;
    }

    setRecording(true);

    const token = await fetch('/realtime-token').then(r => r.text());
    const pc = new RTCPeerConnection();
    pcRef.current = pc;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    stream.getTracks().forEach(t => pc.addTrack(t, stream));

    const dc = pc.createDataChannel('oai-events');
    dc.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.type === 'transcription.delta') onDelta(data.delta);
      if (data.type === 'transcription.completed') {
        setRecording(false);
        onComplete();
      }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const res = await fetch(
      'https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/sdp'
        },
        body: offer.sdp
      }
    );

    await pc.setRemoteDescription({ type: 'answer', sdp: await res.text() });
  }

  return { recording, toggle };
}
