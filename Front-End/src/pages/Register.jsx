import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, ROLE_HOME } from '../context/AuthContext.jsx';
import Navbar from '../components/Navbar.jsx';
import { ROLES } from './Login.jsx';

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ name: '', email: '', password: '', role: 'patient' });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const u = await register(f);
    nav(ROLE_HOME[u.role]);
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <form onSubmit={submit} className="panel mx-auto mt-12 max-w-md space-y-4">
        <h1 className="text-2xl font-bold">Create an account</h1>
        <div><label className="label" htmlFor="n">Full name</label><input id="n" required className="input" value={f.name} onChange={set('name')} /></div>
        <div><label className="label" htmlFor="e">Email</label><input id="e" type="email" required className="input" value={f.email} onChange={set('email')} /></div>
        <div><label className="label" htmlFor="p">Password</label><input id="p" type="password" required minLength={6} className="input" value={f.password} onChange={set('password')} /></div>
        <div><label className="label" htmlFor="r">I am a</label>
          <select id="r" className="input" value={f.role} onChange={set('role')}>{ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        </div>
        <button className="btn-primary w-full">Create account</button>
        <p className="text-sm">Already registered? <Link className="font-bold text-teal underline" to="/login">Sign in</Link></p>
      </form>
    </div>
  );
}
