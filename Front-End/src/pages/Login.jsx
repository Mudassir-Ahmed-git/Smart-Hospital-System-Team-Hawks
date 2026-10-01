import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, ROLE_HOME } from '../context/AuthContext.jsx';
import Navbar from '../components/Navbar.jsx';

export const ROLES = [['patient', 'Patient'], ['hospital', 'Hospital staff'], ['ambulance', 'Ambulance coordinator'], ['admin', 'Administrator']];

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ email: '', password: '', role: 'patient' });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const u = await login(f);
    nav(ROLE_HOME[u.role]);
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <form onSubmit={submit} className="panel mx-auto mt-12 max-w-md space-y-4">
        <h1 className="text-2xl font-bold">Sign in</h1>
        <div><label className="label" htmlFor="email">Email</label><input id="email" type="email" required className="input" value={f.email} onChange={set('email')} /></div>
        <div><label className="label" htmlFor="pw">Password</label><input id="pw" type="password" required className="input" value={f.password} onChange={set('password')} /></div>
        <div><label className="label" htmlFor="role">Sign in as</label>
          <select id="role" className="input" value={f.role} onChange={set('role')}>{ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        </div>
        <button className="btn-primary w-full" disabled={busy}>{busy ? 'Signing in' : 'Sign in'}</button>
        <p className="text-sm">No account? <Link className="font-bold text-teal underline" to="/register">Register</Link></p>
        <p className="text-xs text-ink/60">Demo mode: any email and password works when the API is offline.</p>
      </form>
    </div>
  );
}
