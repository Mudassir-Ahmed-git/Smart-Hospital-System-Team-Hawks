import { NavLink } from 'react-router-dom';
import { FaTachometerAlt, FaSearch, FaBed, FaClipboardList, FaEdit, FaAmbulance, FaRoute, FaExchangeAlt, FaHospital, FaChartBar, FaFileAlt, FaExclamationCircle } from 'react-icons/fa';

const LINKS = {
  patient: [['/patient', 'Dashboard', FaTachometerAlt], ['/patient/search', 'Find a hospital', FaSearch], ['/patient/request', 'Request a bed', FaBed], ['/patient/referrals', 'Referral status', FaClipboardList]],
  hospital: [['/hospital', 'Dashboard', FaTachometerAlt], ['/hospital/capacity', 'Update capacity', FaEdit], ['/hospital/beds', 'Manage beds', FaBed], ['/hospital/emergencies', 'Emergency requests', FaExclamationCircle], ['/hospital/analytics', 'Analytics', FaChartBar]],
  ambulance: [['/ambulance', 'Dashboard', FaAmbulance], ['/ambulance/routing', 'Emergency routing', FaRoute], ['/ambulance/transfer', 'Patient transfer', FaExchangeAlt]],
  admin: [['/admin', 'Dashboard', FaTachometerAlt], ['/admin/hospitals', 'Hospitals', FaHospital], ['/admin/analytics', 'System analytics', FaChartBar], ['/admin/reports', 'Reports', FaFileAlt]],
};

export default function Sidebar({ role, open, onClose }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 w-60 bg-white p-4 pt-16 transition-transform md:static md:z-0 md:translate-x-0 md:pt-4 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {(LINKS[role] || []).map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end onClick={onClose}
              className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2 font-bold ${isActive ? 'bg-teal text-white' : 'hover:bg-teal-soft'}`}>
              <Icon aria-hidden /> {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
