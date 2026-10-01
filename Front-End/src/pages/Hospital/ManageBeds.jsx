import { useEffect, useState } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getWards } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

const STYLE = { Available: 'bg-green-100 text-ok', Occupied: 'bg-red-100 text-signal', Reserved: 'bg-amber-100 text-amber-800', Cleaning: 'bg-teal-soft text-teal-dark' };
const STATES = Object.keys(STYLE);

export default function ManageBeds() {
  const data = useAsync(getWards);
  const [beds, setBeds] = useState(null);
  const [ward, setWard] = useState('All');
  useEffect(() => { if (data) setBeds(data); }, [data]);
  if (!beds) return <LoadingSpinner />;

  const setStatus = (id, status) => setBeds(beds.map((b) => (b.id === id ? { ...b, status, patient: status === 'Available' ? '' : b.patient } : b)));
  const wards = ['All', ...new Set(beds.map((b) => b.ward))];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Manage beds</h1>
      <div className="flex flex-wrap gap-2">
        {wards.map((w) => <button key={w} onClick={() => setWard(w)} className={w === ward ? 'btn-primary' : 'btn-ghost'}>{w}</button>)}
      </div>
      <div className="panel overflow-x-auto p-0">
        <table className="w-full text-left">
          <thead className="bg-mist text-sm"><tr><th className="p-3">Bed</th><th>Ward</th><th>Patient</th><th>Status</th></tr></thead>
          <tbody>
            {beds.filter((b) => ward === 'All' || b.ward === ward).map((b) => (
              <tr key={b.id} className="border-t border-ink/10">
                <td className="p-3 font-bold">{b.id}</td><td>{b.ward}</td><td>{b.patient || '-'}</td>
                <td><select aria-label={`Status for ${b.id}`} value={b.status} onChange={(e) => setStatus(b.id, e.target.value)} className={`rounded px-2 py-1 font-bold ${STYLE[b.status]}`}>
                  {STATES.map((s) => <option key={s}>{s}</option>)}</select></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
