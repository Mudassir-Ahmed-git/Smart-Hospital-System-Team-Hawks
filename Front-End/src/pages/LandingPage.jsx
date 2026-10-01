import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar.jsx';
import MapComponent from '../components/MapComponent.jsx';
import { hospitals } from '../services/mockData.js';
import { FaUserInjured, FaHospital, FaAmbulance, FaUserShield } from 'react-icons/fa';

const ROLES = [
  [FaUserInjured, 'Patients', 'See which hospitals have the bed you need, then request it.'],
  [FaHospital, 'Hospitals', 'Update beds in seconds and respond to incoming emergencies.'],
  [FaAmbulance, 'Ambulance teams', 'Route patients to the nearest hospital with space.'],
  [FaUserShield, 'Administrators', 'Watch capacity across every hospital in one place.'],
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 md:grid-cols-2">
        <div>
          <h1 className="text-4xl font-bold leading-tight md:text-5xl">Find an open bed before the ambulance leaves.</h1>
          <p className="mt-4 max-w-prose text-lg text-ink/80">Live bed counts from every connected hospital, so patients, crews and coordinators send people where care is available.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/register" className="btn-primary">Create an account</Link>
            <Link to="/login" className="btn-ghost">Sign in</Link>
          </div>
        </div>
        <MapComponent hospitals={hospitals} height={360} />
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 pb-16 sm:grid-cols-2 lg:grid-cols-4">
        {ROLES.map(([Icon, t, d]) => (
          <div key={t} className="panel">
            <Icon className="text-2xl text-teal" aria-hidden />
            <h2 className="mt-3 font-bold">{t}</h2>
            <p className="mt-1 text-sm text-ink/70">{d}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
