import { useState } from 'react';
import SearchBar from '../../components/SearchBar.jsx';
import HospitalCard from '../../components/HospitalCard.jsx';
import MapComponent from '../../components/MapComponent.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function SearchHospital() {
  const hs = useAsync(getHospitals);
  const [q, setQ] = useState('');
  const [bed, setBed] = useState('');
  const [sel, setSel] = useState(null);
  if (!hs) return <LoadingSpinner />;

  const list = hs
    .filter((h) => (h.name + h.area + h.specialties.join(' ')).toLowerCase().includes(q.toLowerCase()))
    .filter((h) => !bed || h.beds[bed].available > 0)
    .sort((a, b) => a.distanceKm - b.distanceKm);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Find a hospital</h1>
      <div className="grid gap-3 sm:grid-cols-[1fr_220px]">
        <SearchBar value={q} onChange={setQ} />
        <select className="input" value={bed} onChange={(e) => setBed(e.target.value)} aria-label="Bed type">
          <option value="">Any bed type</option>
          {['ICU', 'General', 'Emergency', 'Ventilator'].map((b) => <option key={b}>{b}</option>)}
        </select>
      </div>
      <MapComponent hospitals={list} selectedId={sel?.id} onSelect={setSel} />
      {sel && <p className="text-sm">Selected: <b>{sel.name}</b></p>}
      {list.length === 0 && <p className="panel">No hospitals match. Clear the bed type filter to see all hospitals.</p>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{list.map((h) => <HospitalCard key={h.id} h={h} />)}</div>
    </div>
  );
}
