import { FaExclamationTriangle } from 'react-icons/fa';

export default function EmergencyAlert({ alerts = [] }) {
  if (!alerts.length) return null;
  return (
    <div role="alert" className="rounded-lg border-2 border-signal bg-red-50 p-4">
      <h2 className="flex items-center gap-2 font-bold text-signal"><FaExclamationTriangle aria-hidden /> Capacity alerts</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        {alerts.map((a, i) => <li key={i}>{a}</li>)}
      </ul>
    </div>
  );
}
