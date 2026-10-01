import { Link } from 'react-router-dom';
import { FaMapMarkerAlt, FaPhoneAlt } from 'react-icons/fa';

export const STATUS_STYLE = {
  normal: ['Normal load', 'bg-green-100 text-ok'],
  busy: ['Busy', 'bg-amber-100 text-amber-800'],
  critical: ['At capacity', 'bg-red-100 text-signal'],
};

export default function HospitalCard({ h }) {
  const [label, cls] = STATUS_STYLE[h.status] || STATUS_STYLE.normal;
  return (
    <article className="panel flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-lg font-bold">{h.name}</h3>
        <span className={`shrink-0 rounded px-2 py-1 text-xs font-bold ${cls}`}>{label}</span>
      </div>
      <p className="flex items-center gap-2 text-sm text-ink/70"><FaMapMarkerAlt aria-hidden /> {h.area}, {h.distanceKm} km away</p>
      <p className="flex items-center gap-2 text-sm text-ink/70"><FaPhoneAlt aria-hidden /> {h.phone}</p>
      <dl className="grid grid-cols-4 gap-2 text-center text-sm">
        {Object.entries(h.beds).map(([k, v]) => (
          <div key={k} className={`rounded p-2 ${v.available === 0 ? 'bg-red-100' : 'bg-mist'}`}>
            <dt className="text-xs text-ink/70">{k}</dt>
            <dd className="text-lg font-bold">{v.available}</dd>
          </div>
        ))}
      </dl>
      <Link to={`/patient/hospitals/${h.id}`} className="btn-primary mt-auto">View details</Link>
    </article>
  );
}
