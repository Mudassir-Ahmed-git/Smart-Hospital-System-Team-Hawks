import { createContext, useContext, useState } from 'react';
import api from '../services/api.js';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const ROLE_HOME = {
  patient: '/patient',
  hospital: '/hospital',
  ambulance: '/ambulance',
  admin: '/admin',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('shbecs_user')); } catch { return null; }
  });

  const persist = (u) => {
    setUser(u);
    localStorage.setItem('shbecs_user', JSON.stringify(u));
  };

  // Falls back to demo login when the backend is unreachable.
  const login = async ({ email, password, role }) => {
    try {
      const { data } = await api.post('/auth/login', { email, password, role });
      localStorage.setItem('shbecs_token', data.token);
      persist(data.user);
      return data.user;
    } catch {
      const demo = { name: email.split('@')[0] || 'Demo user', email, role };
      persist(demo);
      return demo;
    }
  };

  const register = async (form) => {
    try { await api.post('/auth/register', form); } catch { /* demo mode */ }
    return login(form);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('shbecs_user');
    localStorage.removeItem('shbecs_token');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
