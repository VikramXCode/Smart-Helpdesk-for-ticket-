import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import SaasHelpdeskLogin from './pages/SaasHelpdeskLogin';
import CompanyAdminDashboard from './pages/CompanyAdminDashboard';
import CompanyAdminTeamManagement from './pages/CompanyAdminTeamManagement';
import CompanyAdminEmployeeImport from './pages/CompanyAdminEmployeeImport';
import EmployeeDashboard from './pages/EmployeeDashboard';
import ItStaffTicketList from './pages/ItStaffTicketList';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import SuperAdminPlatformMetrics from './pages/SuperAdminPlatformMetrics';
import SuperAdminTenantManagement from './pages/SuperAdminTenantManagement';
import SuperAdminOnboardTenant from './pages/SuperAdminOnboardTenant';
import TicketDetailView from './pages/TicketDetailView';
import KnowledgeBaseGrid from './pages/KnowledgeBaseGrid';
import IssueCenter from './pages/IssueCenter';
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
      <Route path="/dashboard/open" element={
        <ProtectedRoute roles={['employee', 'it_staff', 'company_admin']}>
          <EmployeeDashboard />
        </ProtectedRoute>
      } />
      <Route path="/dashboard/resolved" element={
        <ProtectedRoute roles={['employee', 'it_staff', 'company_admin']}>
          <EmployeeDashboard />
        </ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute roles={['company_admin', 'super_admin']}>
          <CompanyAdminDashboard />
        </ProtectedRoute>
      } />
      <Route path="/admin/team-management" element={
        <ProtectedRoute roles={['company_admin']}>
          <CompanyAdminTeamManagement />
        </ProtectedRoute>
      } />
      <Route path="/admin/employees" element={
        <ProtectedRoute roles={['company_admin']}>
          <CompanyAdminEmployeeImport />
        </ProtectedRoute>
      } />
      <Route path="/staff/tickets" element={
        <ProtectedRoute roles={['it_staff', 'company_admin', 'super_admin']}>
          <ItStaffTicketList />
        </ProtectedRoute>
      } />
      <Route path="/staff/tickets/urgent" element={
        <ProtectedRoute roles={['it_staff', 'company_admin', 'super_admin']}>
          <ItStaffTicketList />
        </ProtectedRoute>
      } />
      <Route path="/staff/tickets/in-progress" element={
        <ProtectedRoute roles={['it_staff', 'company_admin', 'super_admin']}>
          <ItStaffTicketList />
        </ProtectedRoute>
      } />
      <Route path="/staff/tickets/resolved" element={
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
      <Route path="/super-admin/platform-metrics" element={
        <ProtectedRoute roles={['super_admin']}>
          <SuperAdminPlatformMetrics />
        </ProtectedRoute>
      } />
      <Route path="/super-admin/tenants" element={
        <ProtectedRoute roles={['super_admin']}>
          <SuperAdminTenantManagement />
        </ProtectedRoute>
      } />
      <Route path="/super-admin/onboard" element={
        <ProtectedRoute roles={['super_admin']}>
          <SuperAdminOnboardTenant />
        </ProtectedRoute>
      } />
      <Route path="/admin/issues" element={
        <ProtectedRoute roles={['company_admin']}>
          <IssueCenter />
        </ProtectedRoute>
      } />
      <Route path="/super-admin/issues" element={
        <ProtectedRoute roles={['super_admin']}>
          <IssueCenter />
        </ProtectedRoute>
      } />
      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  );
};

export default App;
