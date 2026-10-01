import { useEffect, useState } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getEmergencyRequests } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function EmergencyRequests() {
  const data = useAsync(getEmergencyRequests);
  const [rows, setRows] = useState(null);
  useEffect(() => { if (data) setRows(data.map((r) => ({ ...r, decision: null }))); }, [data]);
  if (!rows) return <LoadingSpinner />;

  const decide = (id, decision) => setRows(rows.map((r) => (r.id === id ? { ...r, decision } : r)));

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Emergency requests</h1>
      {rows.map((r) => (
        <article key={r.id} className={`panel flex flex-wrap items-center justify-between gap-4 ${r.priority === 'Critical' ? 'border-l-8 border-l-signal' : 'border-l-8 border-l-amber'}`}>
          <div>
            <h2 className="font-bold">{r.condition}</h2>
            <p className="text-sm text-ink/70">{r.id} - {r.patient} - needs {r.bedType} bed - {r.source}</p>
            <p className="text-sm font-bold">Arrives in {r.eta}</p>
          </div>
          {r.decision ? <span className="font-bold">{r.decision}</span> : (
            <div className="flex gap-2"><button className="btn-primary" onClick={() => decide(r.id, 'Accepted')}>Accept</button><button className="btn-ghost" onClick={() => decide(r.id, 'Declined')}>Decline</button></div>
          )}
        </article>
      ))}
    </div>
  );
}
