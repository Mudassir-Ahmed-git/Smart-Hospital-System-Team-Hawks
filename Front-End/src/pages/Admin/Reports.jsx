import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getReports } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function Reports() {
  const rows = useAsync(getReports);
  if (!rows) return <LoadingSpinner />;

  const exportCsv = () => {
    const csv = ['Period,Admissions,Transfers,Avg wait,Peak', ...rows.map((r) => [r.period, r.admissions, r.transfers, r.avgWait, r.peak].join(','))].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = 'capacity-report.csv';
    a.click();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">Reports</h1><button className="btn-primary" onClick={exportCsv}>Download CSV</button></div>
      <div className="panel overflow-x-auto p-0">
        <table className="w-full text-left">
          <thead className="bg-mist text-sm"><tr><th className="p-3">Period</th><th>Admissions</th><th>Transfers</th><th>Avg wait</th><th>Peak load</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.period} className="border-t border-ink/10"><td className="p-3 font-bold">{r.period}</td><td>{r.admissions}</td><td>{r.transfers}</td><td>{r.avgWait}</td><td>{r.peak}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
