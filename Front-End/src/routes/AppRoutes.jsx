import { useState } from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuth, ROLE_HOME } from '../context/AuthContext.jsx';
import Navbar from '../components/Navbar.jsx';
import Sidebar from '../components/Sidebar.jsx';

import LandingPage from '../pages/LandingPage.jsx';
import Login from '../pages/Login.jsx';
import Register from '../pages/Register.jsx';
import PatientDashboard from '../pages/Patient/PatientDashboard.jsx';
import SearchHospital from '../pages/Patient/SearchHospital.jsx';
import HospitalDetails from '../pages/Patient/HospitalDetails.jsx';
import BedRequest from '../pages/Patient/BedRequest.jsx';
import ReferralStatus from '../pages/Patient/ReferralStatus.jsx';
import HospitalDashboard from '../pages/Hospital/HospitalDashboard.jsx';
import UpdateCapacity from '../pages/Hospital/UpdateCapacity.jsx';
import ManageBeds from '../pages/Hospital/ManageBeds.jsx';
import EmergencyRequests from '../pages/Hospital/EmergencyRequests.jsx';
import HospitalAnalytics from '../pages/Hospital/HospitalAnalytics.jsx';
import AmbulanceDashboard from '../pages/Ambulance/AmbulanceDashboard.jsx';
import EmergencyRouting from '../pages/Ambulance/EmergencyRouting.jsx';
import PatientTransfer from '../pages/Ambulance/PatientTransfer.jsx';
import AdminDashboard from '../pages/Admin/AdminDashboard.jsx';
import ManageHospitals from '../pages/Admin/ManageHospitals.jsx';
import SystemAnalytics from '../pages/Admin/SystemAnalytics.jsx';
import Reports from '../pages/Admin/Reports.jsx';

function RoleLayout({ role }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />;
  return (
    <div className="min-h-screen">
      <Navbar onMenu={() => setOpen(true)} />
      <div className="flex">
        <Sidebar role={role} open={open} onClose={() => setOpen(false)} />
        <main className="min-w-0 flex-1 p-4 md:p-8"><Outlet /></main>
      </div>
    </div>
  );
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/patient" element={<RoleLayout role="patient" />}>
        <Route index element={<PatientDashboard />} />
        <Route path="search" element={<SearchHospital />} />
        <Route path="hospitals/:id" element={<HospitalDetails />} />
        <Route path="request" element={<BedRequest />} />
        <Route path="referrals" element={<ReferralStatus />} />
      </Route>

      <Route path="/hospital" element={<RoleLayout role="hospital" />}>
        <Route index element={<HospitalDashboard />} />
        <Route path="capacity" element={<UpdateCapacity />} />
        <Route path="beds" element={<ManageBeds />} />
        <Route path="emergencies" element={<EmergencyRequests />} />
        <Route path="analytics" element={<HospitalAnalytics />} />
      </Route>

      <Route path="/ambulance" element={<RoleLayout role="ambulance" />}>
        <Route index element={<AmbulanceDashboard />} />
        <Route path="routing" element={<EmergencyRouting />} />
        <Route path="transfer" element={<PatientTransfer />} />
      </Route>

      <Route path="/admin" element={<RoleLayout role="admin" />}>
        <Route index element={<AdminDashboard />} />
        <Route path="hospitals" element={<ManageHospitals />} />
        <Route path="analytics" element={<SystemAnalytics />} />
        <Route path="reports" element={<Reports />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
