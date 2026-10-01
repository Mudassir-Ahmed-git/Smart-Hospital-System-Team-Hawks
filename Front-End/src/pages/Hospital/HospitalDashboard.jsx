import { Link } from 'react-router-dom';
import { FaBed, FaProcedures, FaLungs, FaAmbulance } from 'react-icons/fa';
import DashboardCard from '../../components/DashboardCard.jsx';
import BedStatusCard from '../../components/BedStatusCard.jsx';
import EmergencyAlert from '../../components/EmergencyAlert.jsx';
import CapacityChart from '../../components/CapacityChart.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospital, getTrend, getEmergencyRequests } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function HospitalDashboard() {
  const h = useAsync(() => getHospital(1));
  const trend = useAsync(getTrend);
  const em = useAsync(getEmergencyRequests);
  if (!h || !trend || !em) return <LoadingSpinner />;

  const alerts = Object.entries(h.beds).filter(([, v]) => v.available / v.total < 0.2).map(([k, v]) => `${k} beds are low: ${v.available} of ${v.total} free.`);
  const free = Object.values(h.beds).reduce((s, v) => s + v.available, 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{h.name}</h1>
      <EmergencyAlert alerts={alerts} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard icon={FaBed} label="Total beds free" value={free} />
        <DashboardCard icon={FaProcedures} label="ICU free" value={h.beds.ICU.available} tone={h.beds.ICU.available < 5 ? 'red' : 'green'} />
        <DashboardCard icon={FaLungs} label="Ventilators free" value={h.beds.Ventilator.available} />
        <DashboardCard icon={FaAmbulance} label="Incoming emergencies" value={em.length} tone="red" hint={<Link to="/hospital/emergencies" className="underline">Review requests</Link>} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(h.beds).map(([k, v]) => <BedStatusCard key={k} type={k} {...v} />)}</div>
      <CapacityChart data={trend} title="Occupancy today" />
    </div>
  );
}
