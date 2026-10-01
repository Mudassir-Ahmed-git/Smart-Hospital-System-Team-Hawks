const TONES = { teal: 'bg-teal-soft text-teal-dark', red: 'bg-red-100 text-signal', amber: 'bg-amber-100 text-amber-800', green: 'bg-green-100 text-ok' };

export default function DashboardCard({ icon: Icon, label, value, hint, tone = 'teal' }) {
  return (
    <div className="panel flex items-start gap-4">
      {Icon && <span className={`rounded-md p-3 text-2xl ${TONES[tone]}`}><Icon aria-hidden /></span>}
      <div>
        <p className="text-sm text-ink/70">{label}</p>
        <p className="text-3xl font-bold">{value}</p>
        {hint && <p className="mt-1 text-sm text-ink/60">{hint}</p>}
      </div>
    </div>
  );
}
