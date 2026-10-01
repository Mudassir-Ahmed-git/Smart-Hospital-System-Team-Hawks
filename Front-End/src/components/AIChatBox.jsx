import { useState, useRef, useEffect } from 'react';
import { FaRobot, FaPaperPlane } from 'react-icons/fa';
import { askAssistant, getHospitals } from '../services/api.js';

// Local fallback so the assistant answers from live bed data even without an AI backend.
async function localReply(text) {
  const hs = await getHospitals();
  const t = text.toLowerCase();
  const type = ['icu', 'ventilator', 'emergency', 'general'].find((k) => t.includes(k));
  if (type) {
    const key = type === 'icu' ? 'ICU' : type[0].toUpperCase() + type.slice(1);
    const best = [...hs].sort((a, b) => b.beds[key].available - a.beds[key].available)[0];
    return `${best.name} has the most ${key} beds free right now: ${best.beds[key].available}. It is ${best.distanceKm} km away.`;
  }
  if (t.includes('nearest') || t.includes('closest')) {
    const n = [...hs].sort((a, b) => a.distanceKm - b.distanceKm)[0];
    return `The closest hospital is ${n.name}, ${n.distanceKm} km away.`;
  }
  return 'Ask me about ICU, emergency, general or ventilator beds, or the nearest hospital.';
}

export default function AIChatBox() {
  const [msgs, setMsgs] = useState([{ from: 'bot', text: 'Hi, I can find hospitals with free beds. What do you need?' }]);
  const [text, setText] = useState('');
  const end = useRef(null);
  useEffect(() => end.current?.scrollIntoView({ behavior: 'smooth' }), [msgs]);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    const q = text.trim();
    setMsgs((m) => [...m, { from: 'user', text: q }]);
    setText('');
    const res = await askAssistant(q);
    const reply = res?.reply || (await localReply(q));
    setMsgs((m) => [...m, { from: 'bot', text: reply }]);
  };

  return (
    <section className="panel flex h-96 flex-col" aria-label="Bed assistant">
      <h3 className="mb-3 flex items-center gap-2 font-bold"><FaRobot aria-hidden className="text-teal" /> Bed assistant</h3>
      <div className="flex-1 space-y-2 overflow-y-auto" aria-live="polite">
        {msgs.map((m, i) => (
          <p key={i} className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${m.from === 'user' ? 'ml-auto bg-teal text-white' : 'bg-mist'}`}>{m.text}</p>
        ))}
        <div ref={end} />
      </div>
      <form onSubmit={send} className="mt-3 flex gap-2">
        <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder="Which hospital has ICU beds?" aria-label="Message" />
        <button className="btn-primary" aria-label="Send"><FaPaperPlane aria-hidden /></button>
      </form>
    </section>
  );
}
