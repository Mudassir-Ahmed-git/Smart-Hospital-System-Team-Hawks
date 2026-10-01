import CapacityChart from '../../components/CapacityChart.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getTrend } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

const BY_DAY = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((name, i) => ({ name, ICU: [62, 65, 60, 70, 78, 84, 72][i], General: [55, 58, 54, 60, 66, 70, 61][i], Emergency: [50, 52, 49, 58, 74, 88, 69][i] }));

export default function HospitalAnalytics() {
  const trend = useAsync(getTrend);
  if (!trend) return <LoadingSpinner />;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Hospital analytics</h1>
      <CapacityChart data={trend} title="Occupancy by hour, today" />
      <CapacityChart data={BY_DAY} type="bar" title="Average occupancy by weekday" />
    </div>
  );
}
