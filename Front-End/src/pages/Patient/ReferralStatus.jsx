import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { getReferrals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

const STYLE = { Accepted: 'bg-green-100 text-ok', Pending: 'bg-amber-100 text-amber-800', Rejected: 'bg-red-100 text-signal' };

export default function ReferralStatus() {
  const refs = useAsync(getReferrals);
  if (!refs) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Referral status</h1>
      {refs.map((r) => (
        <article key={r.id} className="panel flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-bold">{r.hospital}</h2>
            <p className="text-sm text-ink/70">{r.id} - {r.bedType} bed - {r.time}</p>
            <p className="mt-1 text-sm">{r.note}</p>
          </div>
          <span className={`rounded px-3 py-1 text-sm font-bold ${STYLE[r.status]}`}>{r.status}</span>
        </article>
      ))}
    </div>
  );
}
