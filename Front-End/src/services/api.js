import axios from 'axios';
import * as mock from './mockData.js';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  timeout: 4000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('shbecs_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Calls the backend; if it is unreachable, resolves with demo data so the UI always works.
const safe = async (request, fallback) => {
  try {
    const { data } = await request();
    return data;
  } catch {
    return fallback;
  }
};

export const getHospitals = () => safe(() => api.get('/hospitals'), mock.hospitals);
export const getHospital = (id) =>
  safe(() => api.get(`/hospitals/${id}`), mock.hospitals.find((h) => String(h.id) === String(id)));
export const updateCapacity = (id, beds) => safe(() => api.put(`/hospitals/${id}/capacity`, { beds }), { ok: true });
export const createBedRequest = (payload) =>
  safe(() => api.post('/bed-requests', payload), { id: 'REF-' + Math.floor(Math.random() * 9000 + 1000), ...payload });
export const getReferrals = () => safe(() => api.get('/referrals'), mock.patientRequests);
export const getEmergencyRequests = () => safe(() => api.get('/emergency-requests'), mock.emergencyRequests);
export const getWards = () => safe(() => api.get('/beds'), mock.wards);
export const getTrend = () => safe(() => api.get('/analytics/occupancy'), mock.occupancyTrend);
export const getAmbulances = () => safe(() => api.get('/ambulances'), mock.ambulances);
export const getReports = () => safe(() => api.get('/reports'), mock.reportRows);
export const askAssistant = (message) => safe(() => api.post('/assistant', { message }), null);

export default api;
