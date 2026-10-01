import { Link, useParams } from 'react-router-dom';
import BedStatusCard from '../../components/BedStatusCard.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import MapComponent from '../../components/MapComponent.jsx';
import { getHospital } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function HospitalDetails() {
  const { id } = useParams();
  const h = useAsync(() => getHospital(id), [id]);
  if (!h) return <LoadingSpinner />;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{h.name}</h1>
        <p className="text-ink/70">{h.area} - {h.distanceKm} km away - {h.phone}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(h.beds).map(([k, v]) => <BedStatusCard key={k} type={k} {...v} />)}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="panel"><h2 className="mb-2 font-bold">Specialties</h2>
          <ul className="flex flex-wrap gap-2">{h.specialties.map((s) => <li key={s} className="rounded bg-teal-soft px-3 py-1 text-sm font-bold">{s}</li>)}</ul>
          <Link to={`/patient/request?hospital=${h.id}`} className="btn-primary mt-5">Request a bed here</Link>
        </div>
        <MapComponent hospitals={[h]} height={220} />
      </div>
    </div>
  );
}
