import { Link } from 'react-router-dom';
import { FaHospital, FaBed, FaClipboardList } from 'react-icons/fa';
import DashboardCard from '../../components/DashboardCard.jsx';
import HospitalCard from '../../components/HospitalCard.jsx';
import AIChatBox from '../../components/AIChatBox.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { getHospitals, getReferrals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function PatientDashboard() {
  const { user } = useAuth();
  const hs = useAsync(getHospitals);
  const refs = useAsync(getReferrals);
  if (!hs || !refs) return <LoadingSpinner />;
  const nearby = [...hs].sort((a, b) => a.distanceKm - b.distanceKm).slice(0, 2);
  const icu = hs.reduce((s, h) => s + h.beds.ICU.available, 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Welcome, {user.name}</h1>
      <div className="grid gap-4 sm:grid-cols-3">
        <DashboardCard icon={FaHospital} label="Hospitals reporting" value={hs.length} />
        <DashboardCard icon={FaBed} label="ICU beds free nearby" value={icu} tone={icu < 10 ? 'amber' : 'green'} />
        <DashboardCard icon={FaClipboardList} label="Open requests" value={refs.filter((r) => r.status === 'Pending').length} hint="Check Referral status" />
      </div>
      <div className="flex gap-3"><Link to="/patient/request" className="btn-danger">Request an emergency bed</Link><Link to="/patient/search" className="btn-ghost">Find a hospital</Link></div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2">{nearby.map((h) => <HospitalCard key={h.id} h={h} />)}</div>
        <AIChatBox />
      </div>
    </div>
  );
}
