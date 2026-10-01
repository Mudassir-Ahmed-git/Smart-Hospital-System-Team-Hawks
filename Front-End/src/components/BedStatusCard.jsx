export default function BedStatusCard({ type, total, available }) {
  const pct = total ? Math.round((available / total) * 100) : 0;
  const tone = available === 0 ? 'bg-signal' : pct < 20 ? 'bg-amber' : 'bg-ok';
  const word = available === 0 ? 'Full' : pct < 20 ? 'Limited' : 'Available';
  return (
    <div className="panel">
      <div className="flex items-baseline justify-between">
        <h3 className="font-bold">{type}</h3>
        <span className="text-sm font-bold">{word}</span>
      </div>
      <p className="mt-2 text-3xl font-bold">{available}<span className="text-base font-normal text-ink/60"> of {total} free</span></p>
      <div className="mt-3 h-2 rounded bg-mist" role="img" aria-label={`${pct}% of ${type} beds free`}>
        <div className={`h-2 rounded ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
