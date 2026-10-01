import CapacityChart from '../../components/CapacityChart.jsx';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getHospitals, getTrend } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function SystemAnalytics() {
  const hs = useAsync(getHospitals);
  const trend = useAsync(getTrend);
  if (!hs || !trend) return <LoadingSpinner />;
  const pct = (h, k) => Math.round(((h.beds[k].total - h.beds[k].available) / h.beds[k].total) * 100);
  const byHospital = hs.map((h) => ({ name: h.name.split(' ')[0], ICU: pct(h, 'ICU'), General: pct(h, 'General'), Emergency: pct(h, 'Emergency') }));
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">System analytics</h1>
      <CapacityChart data={byHospital} type="bar" title="Occupancy by hospital" />
      <CapacityChart data={trend} title="Network occupancy today" />
    </div>
  );
}
