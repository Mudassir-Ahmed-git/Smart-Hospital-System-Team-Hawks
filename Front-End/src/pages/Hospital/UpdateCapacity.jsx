import { useState, useEffect } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospital, updateCapacity } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function UpdateCapacity() {
  const h = useAsync(() => getHospital(1));
  const [beds, setBeds] = useState(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => { if (h) setBeds(h.beds); }, [h]);
  if (!beds) return <LoadingSpinner />;

  const change = (k, v) => { setSaved(false); setBeds({ ...beds, [k]: { ...beds[k], available: Math.max(0, Math.min(beds[k].total, Number(v) || 0)) } }); };
  const save = async (e) => { e.preventDefault(); await updateCapacity(h.id, beds); setSaved(true); };

  return (
    <form onSubmit={save} className="panel max-w-xl space-y-4">
      <h1 className="text-2xl font-bold">Update capacity</h1>
      <p className="text-sm text-ink/70">Enter the number of beds free right now. Patients and ambulance crews see this immediately.</p>
      {Object.entries(beds).map(([k, v]) => (
        <div key={k} className="grid grid-cols-[1fr_110px] items-center gap-3">
          <label htmlFor={k} className="font-bold">{k} beds free <span className="font-normal text-ink/60">(max {v.total})</span></label>
          <input id={k} type="number" min="0" max={v.total} className="input" value={v.available} onChange={(e) => change(k, e.target.value)} />
        </div>
      ))}
      <button className="btn-primary">Save capacity</button>
      {saved && <p role="status" className="font-bold text-ok">Capacity saved.</p>}
    </form>
  );
}
