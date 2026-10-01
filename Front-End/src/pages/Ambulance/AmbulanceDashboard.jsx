import { FaAmbulance, FaRoute, FaCheckCircle } from 'react-icons/fa';
import DashboardCard from '../../components/DashboardCard.jsx';
import MapComponent from '../../components/MapComponent.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getAmbulances, getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function AmbulanceDashboard() {
  const amb = useAsync(getAmbulances);
  const hs = useAsync(getHospitals);
  if (!amb || !hs) return <LoadingSpinner />;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Ambulance dispatch</h1>
      <div className="grid gap-4 sm:grid-cols-3">
        <DashboardCard icon={FaAmbulance} label="Units active" value={amb.filter((a) => a.status !== 'Available').length} tone="red" />
        <DashboardCard icon={FaCheckCircle} label="Units available" value={amb.filter((a) => a.status === 'Available').length} tone="green" />
        <DashboardCard icon={FaRoute} label="En route now" value={amb.filter((a) => a.status === 'En route').length} />
      </div>
      <MapComponent hospitals={hs} ambulance={{ x: 50, y: 55 }} />
      <div className="panel overflow-x-auto p-0">
        <table className="w-full text-left">
          <thead className="bg-mist text-sm"><tr><th className="p-3">Unit</th><th>Crew</th><th>Status</th><th>Destination</th><th>ETA</th></tr></thead>
          <tbody>{amb.map((a) => <tr key={a.id} className="border-t border-ink/10"><td className="p-3 font-bold">{a.id}</td><td>{a.crew}</td><td>{a.status}</td><td>{a.destination}</td><td>{a.eta}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
