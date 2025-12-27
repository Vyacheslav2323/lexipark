import { Mic, MicOff } from 'lucide-react';

export default function MicButton({ recording, onClick }) {
  return (
    <button type="button" onClick={onClick}>
      {recording ? <MicOff /> : <Mic />}
    </button>
  );
}
