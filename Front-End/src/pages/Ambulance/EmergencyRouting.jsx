import { useState } from 'react';
import MapComponent from '../../components/MapComponent.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function EmergencyRouting() {
  const hs = useAsync(getHospitals);
  const [bed, setBed] = useState('ICU');
  const [sel, setSel] = useState(null);
  if (!hs) return <LoadingSpinner />;

  // Rank by free beds of the needed type, then by distance. Hospitals with none are excluded.
  const ranked = hs.filter((h) => h.beds[bed].available > 0).sort((a, b) => a.distanceKm - b.distanceKm);
  const best = ranked[0];

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Emergency routing</h1>
      <div className="max-w-xs"><label className="label" htmlFor="bt">Bed the patient needs</label>
        <select id="bt" className="input" value={bed} onChange={(e) => { setBed(e.target.value); setSel(null); }}>{['ICU', 'Emergency', 'General', 'Ventilator'].map((b) => <option key={b}>{b}</option>)}</select></div>
      {best ? (
        <div className="panel border-l-8 border-l-ok"><p className="text-sm text-ink/70">Recommended destination</p>
          <p className="text-xl font-bold">{best.name}</p>
          <p>{best.distanceKm} km away, about {Math.round(best.distanceKm * 2.5)} min. {best.beds[bed].available} {bed} beds free.</p></div>
      ) : <p role="alert" className="panel font-bold text-signal">No hospital has a free {bed} bed. Call dispatch to arrange a transfer.</p>}
      <MapComponent hospitals={hs} selectedId={(sel || best)?.id} onSelect={setSel} ambulance={{ x: 50, y: 55 }} />
      <ol className="space-y-2">
        {ranked.map((h) => <li key={h.id} className="panel flex justify-between"><span className="font-bold">{h.name}</span><span>{h.distanceKm} km - {h.beds[bed].available} free</span></li>)}
      </ol>
    </div>
  );
}
