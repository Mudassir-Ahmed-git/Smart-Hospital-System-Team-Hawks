import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

const SERIES = [['ICU', '#D6342C'], ['General', '#0E7C86'], ['Emergency', '#E0A100']];

export default function CapacityChart({ data = [], type = 'line', title, unit = '%' }) {
  const Chart = type === 'bar' ? BarChart : LineChart;
  return (
    <div className="panel">
      {title && <h3 className="mb-3 font-bold">{title}</h3>}
      <div className="h-64">
        <ResponsiveContainer>
          <Chart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#0F2A3320" />
            <XAxis dataKey={data[0]?.time ? 'time' : 'name'} />
            <YAxis unit={unit} />
            <Tooltip />
            <Legend />
            {SERIES.map(([k, c]) => type === 'bar'
              ? <Bar key={k} dataKey={k} fill={c} />
              : <Line key={k} type="monotone" dataKey={k} stroke={c} strokeWidth={2} dot={false} />)}
          </Chart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
