// Lightweight SVG city map for the demo. Swap for Leaflet or Google Maps when a key is available.
const COLORS = { normal: '#2E8B57', busy: '#E0A100', critical: '#D6342C' };

export default function MapComponent({ hospitals = [], ambulance, selectedId, onSelect, height = 340 }) {
  return (
    <div className="overflow-hidden rounded-lg border border-ink/10 bg-teal-soft" style={{ height }}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full" role="img" aria-label="Map of nearby hospitals">
        <path d="M0 30 Q30 20 55 38 T100 50" stroke="#fff" strokeWidth="3" fill="none" />
        <path d="M45 0 Q50 40 38 70 T55 100" stroke="#fff" strokeWidth="2" fill="none" />
        <path d="M0 78 Q40 70 100 82" stroke="#9fd0d5" strokeWidth="5" fill="none" />
        {hospitals.map((h) => (
          <g key={h.id} tabIndex={0} role="button" aria-label={`${h.name}, ${h.status}`} className="cursor-pointer"
             onClick={() => onSelect?.(h)} onKeyDown={(e) => e.key === 'Enter' && onSelect?.(h)}>
            {h.status === 'critical' && <circle cx={h.x} cy={h.y} r="3" fill={COLORS.critical} className="pulse-ring" />}
            <circle cx={h.x} cy={h.y} r={selectedId === h.id ? 3.4 : 2.6} fill={COLORS[h.status]} stroke="#fff" strokeWidth="0.8" />
            <text x={h.x} y={h.y - 4.2} fontSize="3" textAnchor="middle" fill="#0F2A33" fontWeight="700">{h.name.split(' ')[0]}</text>
          </g>
        ))}
        {ambulance && <rect x={ambulance.x - 2} y={ambulance.y - 2} width="4" height="4" fill="#0F2A33" stroke="#fff" strokeWidth="0.6" />}
      </svg>
    </div>
  );
}
