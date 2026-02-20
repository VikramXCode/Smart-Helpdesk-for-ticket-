import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import SaasHelpdeskLogin from './pages/SaasHelpdeskLogin';
import CompanyAdminDashboard from './pages/CompanyAdminDashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';
import ItStaffTicketList from './pages/ItStaffTicketList';
import KnowledgeBaseGrid from './pages/KnowledgeBaseGrid';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import TicketDetailView from './pages/TicketDetailView';
import './App.css';

const RoleRedirect = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  const paths = {
    super_admin: '/super-admin',
    company_admin: '/admin',
    it_staff: '/staff/tickets',
    employee: '/dashboard',
  };
  return <Navigate to={paths[user?.role] || '/dashboard'} replace />;
};

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<SaasHelpdeskLogin />} />
      <Route path="/" element={<RoleRedirect />} />
      <Route path="/dashboard" element={
        <ProtectedRoute roles={['employee', 'it_staff', 'company_admin']}>
          <EmployeeDashboard />
        </ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute roles={['company_admin', 'super_admin']}>
          <CompanyAdminDashboard />
        </ProtectedRoute>
      } />
      <Route path="/staff/tickets" element={
        <ProtectedRoute roles={['it_staff', 'company_admin', 'super_admin']}>
          <ItStaffTicketList />
        </ProtectedRoute>
      } />
      <Route path="/tickets/:ticketId" element={
        <ProtectedRoute roles={['employee', 'it_staff', 'company_admin', 'super_admin']}>
          <TicketDetailView />
        </ProtectedRoute>
      } />
      <Route path="/knowledge" element={
        <ProtectedRoute roles={['employee', 'it_staff', 'company_admin', 'super_admin']}>
          <KnowledgeBaseGrid />
        </ProtectedRoute>
      } />
      <Route path="/super-admin" element={
        <ProtectedRoute roles={['super_admin']}>
          <SuperAdminDashboard />
        </ProtectedRoute>
      } />
      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  );
};

export default App;
