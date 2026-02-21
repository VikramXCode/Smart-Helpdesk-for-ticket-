import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useAuth } from '../context/AuthContext';

export const AdminLayout = ({ children, title, headerAction }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  const role = user?.role;
  const isSuperAdmin = role === 'super_admin';
  const isCompanyAdmin = role === 'company_admin';
  const isItStaff = role === 'it_staff';
  const isEmployee = role === 'employee';

  const dashboardLink = isSuperAdmin
    ? '/super-admin'
    : isCompanyAdmin
      ? '/admin'
      : isItStaff
        ? '/staff/tickets'
        : '/dashboard';

  const dashboardLabel = isSuperAdmin
    ? 'Dashboard'
    : isItStaff
      ? 'Tickets'
      : 'Dashboard';

  const showTicketsLink = isCompanyAdmin;
  const showKnowledgeLink = false;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="w-full">
      <div className="flex h-screen w-full overflow-hidden">
        {/* Mobile sidebar overlay */}
        {showMobileSidebar && (
          <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setShowMobileSidebar(false)} />
        )}

        {/* Sidebar */}
        <div className={`fixed lg:relative z-50 flex flex-col w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 h-full flex-shrink-0 transition-transform lg:transition-none ${showMobileSidebar ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
          <div className="p-6 flex items-center gap-3">
            <div className="size-10 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-xl">
              <span className="material-symbols-outlined">smart_toy</span>
            </div>
            <div className="flex flex-col flex-1">
              <h1 className="text-primary dark:text-white text-base font-bold leading-tight">HelpDesk AI</h1>
              <p className="text-slate-500 text-xs font-medium">{(role || 'user').replace('_', ' ')} portal</p>
            </div>
            <button onClick={() => setShowMobileSidebar(false)} className="lg:hidden p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors">
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
          <nav className="flex flex-col gap-1 px-4 py-4 flex-1">
            <Link to={dashboardLink} onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined">dashboard</span><span className="text-sm font-medium">{dashboardLabel}</span>
            </Link>
            {isSuperAdmin && (
              <>
                <Link to="/super-admin/platform-metrics" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">monitoring</span><span className="text-sm font-medium">Platform Metrics</span>
                </Link>
                <Link to="/super-admin/tenants" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">apartment</span><span className="text-sm font-medium">Tenant Management</span>
                </Link>
                <Link to="/super-admin/onboard" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">add_business</span><span className="text-sm font-medium">Onboard Tenant</span>
                </Link>
                <Link to="/super-admin/issues" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">forum</span><span className="text-sm font-medium">Issue Inbox</span>
                </Link>
              </>
            )}
            {showTicketsLink && (
              <Link to="/staff/tickets" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                <span className="material-symbols-outlined">confirmation_number</span><span className="text-sm font-medium">Tickets</span>
              </Link>
            )}
            {isItStaff && (
              <>
                <Link to="/staff/tickets/urgent" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">priority_high</span><span className="text-sm font-medium">Urgent Queue</span>
                </Link>
                <Link to="/staff/tickets/in-progress" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">timelapse</span><span className="text-sm font-medium">In Progress</span>
                </Link>
                <Link to="/staff/tickets/resolved" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">task_alt</span><span className="text-sm font-medium">Resolved</span>
                </Link>
              </>
            )}
            {isEmployee && (
              <>
                <Link to="/dashboard/open" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">pending_actions</span><span className="text-sm font-medium">Open Tickets</span>
                </Link>
                <Link to="/dashboard/resolved" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                  <span className="material-symbols-outlined">task_alt</span><span className="text-sm font-medium">Resolved Tickets</span>
                </Link>
              </>
            )}
            {isCompanyAdmin && (
              <Link to="/admin/team-management" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                <span className="material-symbols-outlined">groups</span><span className="text-sm font-medium">Team Management</span>
              </Link>
            )}
            {isCompanyAdmin && (
              <Link to="/admin/employees" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                <span className="material-symbols-outlined">badge</span><span className="text-sm font-medium">Employees</span>
              </Link>
            )}
            {isCompanyAdmin && (
              <Link to="/admin/issues" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                <span className="material-symbols-outlined">forum</span><span className="text-sm font-medium">Issues</span>
              </Link>
            )}
            {showKnowledgeLink && (
              <Link to="/knowledge" onClick={() => setShowMobileSidebar(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
                <span className="material-symbols-outlined">book</span><span className="text-sm font-medium">Knowledge Base</span>
              </Link>
            )}
            <div className="my-4 border-t border-slate-100 dark:border-slate-700"></div>
            <button onClick={handleLogout} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors w-full text-left">
              <span className="material-symbols-outlined">logout</span><span className="text-sm font-medium">Sign Out</span>
            </button>
          </nav>
          <div className="p-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3 p-2 rounded-lg">
              <div className="size-9 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm">{user?.full_name?.charAt(0)}</div>
              <div className="flex flex-col overflow-hidden">
                <p className="text-slate-900 dark:text-white text-sm font-medium truncate">{user?.full_name}</p>
                <p className="text-slate-500 text-xs truncate">{user?.role?.replace('_', ' ')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-background-light dark:bg-slate-900">
          <header className="flex items-center justify-between px-4 sm:px-8 py-5 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
            <div className="flex items-center gap-4">
              <button onClick={() => setShowMobileSidebar(true)} className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                <span className="material-symbols-outlined">menu</span>
              </button>
              <div className="flex flex-col gap-1">
                <h2 className="text-xl sm:text-2xl font-bold text-primary dark:text-white tracking-tight">{title}</h2>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {headerAction}
            </div>
          </header>

          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};

AdminLayout.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  headerAction: PropTypes.node,
};
