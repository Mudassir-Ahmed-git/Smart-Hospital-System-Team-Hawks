import { useEffect, useState } from 'react';
import SearchBar from '../../components/SearchBar.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { STATUS_STYLE } from '../../components/HospitalCard.jsx';
import { getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function ManageHospitals() {
  const data = useAsync(getHospitals);
  const [rows, setRows] = useState(null);
  const [q, setQ] = useState('');
  const [name, setName] = useState('');
  useEffect(() => { if (data) setRows(data); }, [data]);
  if (!rows) return <LoadingSpinner />;

  const add = (e) => {
    e.preventDefault();
    const z = { total: 10, available: 10 };
    setRows([...rows, { id: Date.now(), name, area: 'New area', distanceKm: 0, phone: '-', x: 50, y: 50, specialties: [], status: 'normal', beds: { ICU: z, General: z, Emergency: z, Ventilator: z } }]);
    setName('');
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Manage hospitals</h1>
      <form onSubmit={add} className="panel flex flex-wrap gap-3">
        <input aria-label="Hospital name" required className="input max-w-sm" placeholder="New hospital name" value={name} onChange={(e) => setName(e.target.value)} />
        <button className="btn-primary">Add hospital</button>
      </form>
      <SearchBar value={q} onChange={setQ} placeholder="Search hospitals" />
      <div className="panel overflow-x-auto p-0">
        <table className="w-full text-left">
          <thead className="bg-mist text-sm"><tr><th className="p-3">Hospital</th><th>Area</th><th>ICU free</th><th>Status</th><th /></tr></thead>
          <tbody>
            {rows.filter((h) => h.name.toLowerCase().includes(q.toLowerCase())).map((h) => (
              <tr key={h.id} className="border-t border-ink/10">
                <td className="p-3 font-bold">{h.name}</td><td>{h.area}</td><td>{h.beds.ICU.available}</td>
                <td><span className={`rounded px-2 py-1 text-xs font-bold ${STATUS_STYLE[h.status][1]}`}>{STATUS_STYLE[h.status][0]}</span></td>
                <td><button className="font-bold text-signal underline" onClick={() => setRows(rows.filter((r) => r.id !== h.id))}>Remove</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
