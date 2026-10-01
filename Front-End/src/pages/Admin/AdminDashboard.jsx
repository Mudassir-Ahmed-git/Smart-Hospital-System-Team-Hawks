import { FaHospital, FaBed, FaAmbulance, FaExclamationTriangle } from 'react-icons/fa';
import DashboardCard from '../../components/DashboardCard.jsx';
import EmergencyAlert from '../../components/EmergencyAlert.jsx';
import MapComponent from '../../components/MapComponent.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospitals, getAmbulances } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function AdminDashboard() {
  const hs = useAsync(getHospitals);
  const amb = useAsync(getAmbulances);
  if (!hs || !amb) return <LoadingSpinner />;
  const total = (k) => hs.reduce((s, h) => s + h.beds[k].total, 0);
  const free = (k) => hs.reduce((s, h) => s + h.beds[k].available, 0);
  const critical = hs.filter((h) => h.status === 'critical');

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">System overview</h1>
      <EmergencyAlert alerts={critical.map((h) => `${h.name} is at capacity.`)} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard icon={FaHospital} label="Hospitals connected" value={hs.length} />
        <DashboardCard icon={FaBed} label="ICU beds free" value={`${free('ICU')} / ${total('ICU')}`} tone="amber" />
        <DashboardCard icon={FaAmbulance} label="Ambulances active" value={amb.filter((a) => a.status !== 'Available').length} />
        <DashboardCard icon={FaExclamationTriangle} label="Hospitals at capacity" value={critical.length} tone={critical.length ? 'red' : 'green'} />
      </div>
      <MapComponent hospitals={hs} />
    </div>
  );
}
