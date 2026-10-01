import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { createBedRequest, getHospitals } from '../../services/api.js';
import useAsync from '../../services/useAsync.js';

export default function BedRequest() {
  const [params] = useSearchParams();
  const hs = useAsync(getHospitals);
  const [f, setF] = useState({ hospitalId: params.get('hospital') || '', bedType: 'General', priority: 'Normal', patientName: '', condition: '' });
  const [done, setDone] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  if (!hs) return <LoadingSpinner />;

  const submit = async (e) => {
    e.preventDefault();
    setDone(await createBedRequest(f));
  };

  if (done) return (
    <div className="panel max-w-xl space-y-3" role="status">
      <h1 className="text-2xl font-bold">Request sent</h1>
      <p>Your reference is <b>{done.id}</b>. The hospital will respond shortly.</p>
      <Link to="/patient/referrals" className="btn-primary">Track referral status</Link>
    </div>
  );

  const chosen = hs.find((h) => String(h.id) === String(f.hospitalId));
  const full = chosen && chosen.beds[f.bedType].available === 0;

  return (
    <form onSubmit={submit} className="panel max-w-xl space-y-4">
      <h1 className="text-2xl font-bold">Request a bed</h1>
      <div><label className="label" htmlFor="pn">Patient name</label><input id="pn" required className="input" value={f.patientName} onChange={set('patientName')} /></div>
      <div><label className="label" htmlFor="h">Hospital</label>
        <select id="h" required className="input" value={f.hospitalId} onChange={set('hospitalId')}>
          <option value="">Choose a hospital</option>{hs.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
        </select></div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div><label className="label" htmlFor="b">Bed type</label>
          <select id="b" className="input" value={f.bedType} onChange={set('bedType')}>{['ICU', 'General', 'Emergency', 'Ventilator'].map((b) => <option key={b}>{b}</option>)}</select></div>
        <div><label className="label" htmlFor="pr">Priority</label>
          <select id="pr" className="input" value={f.priority} onChange={set('priority')}>{['Normal', 'High', 'Critical'].map((b) => <option key={b}>{b}</option>)}</select></div>
      </div>
      <div><label className="label" htmlFor="c">Condition</label><textarea id="c" rows="3" required className="input" value={f.condition} onChange={set('condition')} /></div>
      {full && <p role="alert" className="rounded bg-red-50 p-3 text-sm font-bold text-signal">{chosen.name} has no {f.bedType} beds free. Choose another hospital or bed type.</p>}
      <button className="btn-primary" disabled={full}>Send request</button>
    </form>
  );
}
