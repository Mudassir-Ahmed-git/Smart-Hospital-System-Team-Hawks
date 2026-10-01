import { useState } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

const STEPS = ['Patient picked up', 'En route to hospital', 'Arrived at hospital', 'Handover complete'];

export default function PatientTransfer() {
  const hs = useAsync(getHospitals);
  const [f, setF] = useState({ patient: '', from: '', to: '', notes: '' });
  const [step, setStep] = useState(-1);
  if (!hs) return <LoadingSpinner />;
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={(e) => { e.preventDefault(); setStep(0); }} className="panel space-y-4">
        <h1 className="text-2xl font-bold">Patient transfer</h1>
        <div><label className="label" htmlFor="p">Patient</label><input id="p" required className="input" value={f.patient} onChange={set('patient')} /></div>
        <div><label className="label" htmlFor="f">Pickup location</label><input id="f" required className="input" value={f.from} onChange={set('from')} /></div>
        <div><label className="label" htmlFor="t">Destination hospital</label>
          <select id="t" required className="input" value={f.to} onChange={set('to')}><option value="">Choose a hospital</option>{hs.map((h) => <option key={h.id}>{h.name}</option>)}</select></div>
        <div><label className="label" htmlFor="n">Clinical notes</label><textarea id="n" rows="3" className="input" value={f.notes} onChange={set('notes')} /></div>
        <button className="btn-primary" disabled={step >= 0}>Start transfer</button>
      </form>
      <div className="panel">
        <h2 className="mb-4 font-bold">Transfer progress</h2>
        {step < 0 ? <p className="text-ink/70">Start a transfer to track it here.</p> : (
          <>
            <ol className="space-y-3">
              {STEPS.map((s, i) => <li key={s} className={`flex items-center gap-3 ${i <= step ? 'font-bold' : 'text-ink/50'}`}><span className={`h-4 w-4 rounded-full ${i <= step ? 'bg-ok' : 'bg-ink/20'}`} />{s}</li>)}
            </ol>
            {step < STEPS.length - 1
              ? <button className="btn-primary mt-5" onClick={() => setStep(step + 1)}>Mark: {STEPS[step + 1]}</button>
              : <p role="status" className="mt-5 font-bold text-ok">Transfer complete. {f.to} has been notified.</p>}
          </>
        )}
      </div>
    </div>
  );
}
