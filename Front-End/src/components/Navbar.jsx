import { Link, useNavigate } from 'react-router-dom';
import { FaHospital, FaBars, FaSignOutAlt } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext.jsx';

export default function Navbar({ onMenu }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between bg-ink px-4 py-3 text-white">
      <div className="flex items-center gap-3">
        {onMenu && <button className="md:hidden" onClick={onMenu} aria-label="Open menu"><FaBars /></button>}
        <Link to="/" className="flex items-center gap-2 font-bold"><FaHospital aria-hidden /> Smart Bed System</Link>
      </div>
      {user ? (
        <div className="flex items-center gap-4 text-sm">
          <span className="hidden sm:inline">{user.name} ({user.role})</span>
          <button className="flex items-center gap-1 hover:underline" onClick={() => { logout(); nav('/login'); }}><FaSignOutAlt aria-hidden /> Sign out</button>
        </div>
      ) : (
        <div className="flex gap-3 text-sm">
          <Link to="/login" className="hover:underline">Sign in</Link>
          <Link to="/register" className="rounded bg-teal px-3 py-1 font-bold">Register</Link>
        </div>
      )}
    </header>
  );
}
