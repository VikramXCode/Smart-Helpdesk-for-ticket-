import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children, roles }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background-light dark:bg-background-dark">
        <div className="flex flex-col items-center gap-3">
          <div className="size-10 rounded-lg bg-primary flex items-center justify-center text-white animate-pulse">
            <span className="material-symbols-outlined">smart_toy</span>
          </div>
          <p className="text-slate-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user?.role)) {
    // Redirect to the user's default page based on role
    const defaultPaths = {
      super_admin: '/super-admin',
      company_admin: '/admin',
      it_staff: '/staff/tickets',
      employee: '/dashboard',
    };
    return <Navigate to={defaultPaths[user?.role] || '/dashboard'} replace />;
  }

  return children;
};

export default ProtectedRoute;
