import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AdminLayout } from '../components/AdminLayout';
import { listTickets } from '../api/tickets';
import { changePassword } from '../api/auth';
import toast from 'react-hot-toast';

const ItStaffTicketList = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [search, setSearch] = useState('');

  // Stats
  const [stats, setStats] = useState({ open: 0, pending: 0, urgent: 0, resolved: 0 });
  const [showForcePasswordModal, setShowForcePasswordModal] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' });

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit, sort: 'created_at', order: 'desc' };
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (search) params.search = search;

      const res = await listTickets(params);
      setTickets(res.data.tickets || []);
      setTotal(res.data.total || 0);

      // Compute stats from unfiltered count (we approximate from current data)
      const all = res.data.tickets || [];
      setStats({
        open: all.filter(t => ['new', 'open', 'assigned'].includes(t.status)).length,
        pending: all.filter(t => t.status === 'pending' || t.status === 'in_progress').length,
        urgent: all.filter(t => t.priority === 'critical' || t.priority === 'high').length,
        resolved: all.filter(t => ['resolved', 'closed', 'auto_resolved'].includes(t.status)).length,
      });
    } catch (err) {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  }, [page, limit, statusFilter, priorityFilter, categoryFilter, search]);

  useEffect(() => { loadTickets(); }, [loadTickets]);
  useEffect(() => {
    if (user?.role === 'it_staff' && user?.password_change_required) {
      setShowForcePasswordModal(true);
      setPasswordForm((prev) => ({ ...prev, current: prev.current || '12345678' }));
    }
  }, [user]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const statusParam = params.get('status') || '';
    const priorityParam = params.get('priority') || '';
    const categoryParam = params.get('category') || '';

    let routeStatus = '';
    let routePriority = '';
    if (location.pathname === '/staff/tickets/urgent') {
      routePriority = 'critical';
    } else if (location.pathname === '/staff/tickets/in-progress') {
      routeStatus = 'in_progress';
    } else if (location.pathname === '/staff/tickets/resolved') {
      routeStatus = 'resolved';
    }

    setStatusFilter(routeStatus || statusParam);
    setPriorityFilter(routePriority || priorityParam);
    setCategoryFilter(categoryParam);
    setPage(1);
  }, [location.pathname, location.search]);

  const handleForcePasswordChange = async (e) => {
    e.preventDefault();
    if (!passwordForm.current || !passwordForm.next || !passwordForm.confirm) {
      toast.error('Please fill all password fields');
      return;
    }
    if (passwordForm.next !== passwordForm.confirm) {
      toast.error('New password and confirmation do not match');
      return;
    }
    if (passwordForm.next.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }

    try {
      setChangingPassword(true);
      await changePassword(passwordForm.current, passwordForm.next);
      await refreshUser();
      setShowForcePasswordModal(false);
      setPasswordForm({ current: '', next: '', confirm: '' });
      toast.success('Password updated successfully');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update password');
    } finally {
      setChangingPassword(false);
    }
  };

  const clearFilters = () => {
    setStatusFilter(''); setPriorityFilter(''); setCategoryFilter(''); setSearch(''); setPage(1);
  };

  const totalPages = Math.ceil(total / limit);

  const activeQueueLabel =
    location.pathname === '/staff/tickets/urgent'
      ? 'Urgent Queue'
      : location.pathname === '/staff/tickets/in-progress'
        ? 'In Progress Queue'
        : location.pathname === '/staff/tickets/resolved'
          ? 'Resolved Queue'
          : 'All Tickets';

  const categorySummary = Object.entries(
    tickets.reduce((acc, ticket) => {
      const key = ticket.category || 'Uncategorized';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {})
  )
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const urgentTickets = tickets
    .filter((ticket) => ['critical', 'high'].includes(ticket.priority))
    .slice(0, 5);

  const priorityBadge = (p) => {
    const map = {
      critical: 'bg-red-50 text-red-700 border-red-100',
      high: 'bg-orange-50 text-orange-700 border-orange-100',
      medium: 'bg-amber-50 text-amber-700 border-amber-100',
      low: 'bg-slate-100 text-slate-600 border-slate-200',
    };
    return map[p] || map.medium;
  };

  const priorityDot = (p) => {
    const map = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-amber-500', low: 'bg-slate-400' };
    return map[p] || map.medium;
  };

  const statusBadge = (s) => {
    const map = {
      new: 'bg-blue-50 text-blue-700 border-blue-200',
      assigned: 'bg-sky-50 text-sky-700 border-sky-200',
      in_progress: 'bg-sky-50 text-sky-700 border-sky-200',
      pending: 'bg-amber-50 text-amber-700 border-amber-200',
      resolved: 'bg-green-50 text-green-700 border-green-200',
      closed: 'bg-slate-100 text-slate-600 border-slate-200',
      auto_resolved: 'bg-purple-50 text-purple-700 border-purple-200',
    };
    return map[s] || 'bg-green-50 text-green-700 border-green-200';
  };

  const statusIcon = (s) => {
    const map = {
      new: 'radio_button_checked', assigned: 'person', in_progress: 'timelapse',
      pending: 'hourglass_empty', resolved: 'check_circle', closed: 'cancel', auto_resolved: 'auto_awesome',
    };
    return map[s] || 'radio_button_checked';
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  const headerAction = (
    <div className="hidden md:flex relative group">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 material-symbols-outlined text-[20px]">search</span>
      <input className="pl-10 pr-4 py-2 w-64 text-sm bg-slate-50 border-none ring-1 ring-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:bg-white transition-all placeholder:text-slate-400"
        placeholder="Search tickets..." type="text" value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
    </div>
  );

  return (
    <AdminLayout title="Ticket Management" headerAction={headerAction}>
      <div className="p-4 md:p-6 lg:p-8">
        <div className="max-w-[1400px] mx-auto flex flex-col gap-6">
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">dashboard</span>
                  <p className="text-sm font-semibold text-slate-900">{activeQueueLabel}</p>
                </div>
                <span className="text-xs text-slate-500">Route: {location.pathname}</span>
              </div>

              {/* Stat cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div><p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Open</p><p className="text-2xl font-bold text-slate-900 mt-1">{stats.open}</p></div>
                  <div className="bg-blue-50 text-blue-600 p-2 rounded-lg"><span className="material-symbols-outlined">inbox</span></div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div><p className="text-slate-500 text-xs font-medium uppercase tracking-wider">In Progress</p><p className="text-2xl font-bold text-slate-900 mt-1">{stats.pending}</p></div>
                  <div className="bg-amber-50 text-amber-600 p-2 rounded-lg"><span className="material-symbols-outlined">pending</span></div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div><p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Urgent</p><p className="text-2xl font-bold text-slate-900 mt-1">{stats.urgent}</p></div>
                  <div className="bg-red-50 text-red-600 p-2 rounded-lg"><span className="material-symbols-outlined">error</span></div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div><p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Resolved</p><p className="text-2xl font-bold text-slate-900 mt-1">{stats.resolved}</p></div>
                  <div className="bg-green-50 text-green-600 p-2 rounded-lg"><span className="material-symbols-outlined">check_circle</span></div>
                </div>
              </div>

              {/* Filters */}
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto px-1">
                  <select className="appearance-none bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg w-32 pl-3 pr-8 py-2 cursor-pointer hover:bg-slate-100 transition-colors"
                    value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
                    <option value="">Status: All</option>
                    <option value="new">New</option>
                    <option value="assigned">Assigned</option>
                    <option value="in_progress">In Progress</option>
                    <option value="pending">Pending</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                  <select className="appearance-none bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg w-32 pl-3 pr-8 py-2 cursor-pointer hover:bg-slate-100 transition-colors"
                    value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}>
                    <option value="">Priority: All</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <select className="appearance-none bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg w-36 pl-3 pr-8 py-2 cursor-pointer hover:bg-slate-100 transition-colors"
                    value={categoryFilter} onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}>
                    <option value="">Category: All</option>
                    <option value="Hardware">Hardware</option>
                    <option value="Software">Software</option>
                    <option value="Network">Network</option>
                    <option value="Access">Access</option>
                  </select>
                  <button onClick={clearFilters} className="text-sm text-primary font-medium hover:underline whitespace-nowrap px-2">Clear filters</button>
                </div>
                <div className="flex items-center gap-2 px-2 sm:px-0 ml-auto">
                  <span className="text-xs text-slate-500">Showing {(page - 1) * limit + 1}-{Math.min(page * limit, total)} of {total}</span>
                </div>
              </div>

              {/* Table */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50/50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                        <th className="px-6 py-4">ID</th>
                        <th className="px-6 py-4 w-1/3">Subject</th>
                        <th className="px-6 py-4">Category</th>
                        <th className="px-6 py-4">Priority</th>
                        <th className="px-6 py-4">Status</th>
                        <th className="px-6 py-4 text-right">Created</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {loading ? (
                        <tr><td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                          <span className="material-symbols-outlined animate-spin text-2xl">progress_activity</span>
                          <p className="mt-2 text-sm">Loading tickets...</p>
                        </td></tr>
                      ) : tickets.length === 0 ? (
                        <tr><td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                          <span className="material-symbols-outlined text-3xl mb-2">inbox</span>
                          <p className="text-sm">No tickets found</p>
                        </td></tr>
                      ) : tickets.map((ticket) => (
                        <tr key={ticket.id} className="hover:bg-slate-50/80 transition-colors group cursor-pointer" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                          <td className="px-6 py-4 text-sm font-mono text-slate-500">{ticket.ticket_number}</td>
                          <td className="px-6 py-4">
                            <div className="flex flex-col">
                              <span className="text-sm font-semibold text-slate-900 group-hover:text-primary transition-colors">{ticket.title}</span>
                              {ticket.ai_suggestion && (
                                <div className="flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-medium border border-purple-100 w-fit">
                                  <span className="material-symbols-outlined text-[10px]">auto_awesome</span> AI Insight
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                              {ticket.category || 'Uncategorized'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${priorityBadge(ticket.priority)}`}>
                              <span className={`size-1.5 rounded-full ${priorityDot(ticket.priority)}`}></span>
                              {ticket.priority?.charAt(0).toUpperCase() + ticket.priority?.slice(1)}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge(ticket.status)}`}>
                              <span className="material-symbols-outlined text-[14px]">{statusIcon(ticket.status)}</span>
                              {ticket.status?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right text-sm text-slate-500">{timeAgo(ticket.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between border-t border-slate-200 bg-white px-6 py-3">
                    <p className="text-sm text-slate-700">
                      Showing <span className="font-medium">{(page - 1) * limit + 1}</span> to <span className="font-medium">{Math.min(page * limit, total)}</span> of <span className="font-medium">{total}</span> results
                    </p>
                    <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm">
                      <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                        className="relative inline-flex items-center rounded-l-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 disabled:opacity-50">
                        <span className="material-symbols-outlined text-sm">chevron_left</span>
                      </button>
                      {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map(p => (
                        <button key={p} onClick={() => setPage(p)}
                          className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${p === page ? 'bg-primary text-white z-10' : 'text-slate-900 ring-1 ring-inset ring-slate-300 hover:bg-slate-50'}`}>
                          {p}
                        </button>
                      ))}
                      <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                        className="relative inline-flex items-center rounded-r-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 disabled:opacity-50">
                        <span className="material-symbols-outlined text-sm">chevron_right</span>
                      </button>
                    </nav>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl shadow-sm p-5">
                  <h3 className="text-sm font-bold text-slate-900 mb-4">Category Load Distribution</h3>
                  {categorySummary.length === 0 ? (
                    <p className="text-sm text-slate-500">No category data available.</p>
                  ) : (
                    <div className="space-y-3">
                      {categorySummary.map(([name, count]) => {
                        const max = Math.max(1, ...categorySummary.map((entry) => entry[1]));
                        return (
                          <div key={name} className="flex items-center gap-3">
                            <span className="text-sm text-slate-700 w-40 truncate">{name}</span>
                            <div className="flex-1 bg-slate-100 rounded-full h-3">
                              <div className="h-3 rounded-full bg-gradient-to-r from-primary to-blue-400" style={{ width: `${(count / max) * 100}%` }} />
                            </div>
                            <span className="text-xs font-bold text-slate-700 w-10 text-right">{count}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5">
                  <h3 className="text-sm font-bold text-slate-900 mb-4">Urgent Queue</h3>
                  {urgentTickets.length === 0 ? (
                    <p className="text-sm text-slate-500">No urgent tickets in this view.</p>
                  ) : (
                    <div className="space-y-3">
                      {urgentTickets.map((ticket) => (
                        <button
                          key={ticket.id}
                          onClick={() => navigate(`/tickets/${ticket.id}`)}
                          className="w-full text-left rounded-lg border border-slate-200 p-3 hover:bg-slate-50 transition-colors"
                        >
                          <p className="text-sm font-semibold text-slate-900 truncate">{ticket.title}</p>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-xs text-slate-500 font-mono">{ticket.ticket_number}</span>
                            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] border ${priorityBadge(ticket.priority)}`}>
                              <span className={`size-1.5 rounded-full ${priorityDot(ticket.priority)}`}></span>
                              {ticket.priority}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
      </div>

      {showForcePasswordModal && (
        <div className="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Change Default Password</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">For security, you must change your default agent password before continuing.</p>
            <form onSubmit={handleForcePasswordChange} className="space-y-3">
              <input
                type="password"
                placeholder="Current password"
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                value={passwordForm.current}
                onChange={(e) => setPasswordForm((prev) => ({ ...prev, current: e.target.value }))}
                required
              />
              <input
                type="password"
                placeholder="New password"
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                value={passwordForm.next}
                onChange={(e) => setPasswordForm((prev) => ({ ...prev, next: e.target.value }))}
                required
              />
              <input
                type="password"
                placeholder="Confirm new password"
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                value={passwordForm.confirm}
                onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm: e.target.value }))}
                required
              />
              <button type="submit" disabled={changingPassword} className="w-full px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-60">
                {changingPassword ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default ItStaffTicketList;
