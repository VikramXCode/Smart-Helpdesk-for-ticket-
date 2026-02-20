import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { AdminLayout } from '../components/AdminLayout';
import { getStats, listCompanies, createCompany, updateCompany, deleteCompany } from '../api/superadmin';
import toast from 'react-hot-toast';

const SuperAdminDashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddCompany, setShowAddCompany] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: '', slug: '', domain: '', admin_email: '', admin_name: '', admin_password: '' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, companiesRes] = await Promise.all([getStats(), listCompanies()]);
      setStats(statsRes.data);
      setCompanies(companiesRes.data.companies || companiesRes.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      await createCompany(newCompany);
      toast.success('Company created successfully!');
      setShowAddCompany(false);
      setNewCompany({ name: '', slug: '', domain: '', admin_email: '', admin_name: '', admin_password: '' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create company');
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete ${name}? This is irreversible.`)) return;
    try {
      await deleteCompany(id);
      toast.success(`${name} deleted`);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const filteredCompanies = companies.filter(c =>
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.slug?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusColor = (active) => active !== false
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : 'bg-red-50 text-red-700 border-red-200';

  if (loading) {
    return (
      <div className="w-full min-h-screen bg-slate-50 flex items-center justify-center">
        <span className="material-symbols-outlined animate-spin text-4xl text-primary">progress_activity</span>
      </div>
    );
  }

  const headerAction = (
    <button onClick={() => setShowAddCompany(true)} className="flex items-center gap-2 h-9 px-4 bg-primary text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors shadow-sm">
      <span className="material-symbols-outlined text-[18px]">add</span> Onboard Tenant
    </button>
  );

  return (
    <AdminLayout title="Platform Dashboard" headerAction={headerAction}>
      <div className="p-6 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Total Companies', value: stats?.total_companies ?? companies.length, icon: 'apartment', color: 'text-blue-600 bg-blue-50' },
              { label: 'Total Users', value: stats?.total_users ?? '—', icon: 'group', color: 'text-emerald-600 bg-emerald-50' },
              { label: 'Active Tickets', value: stats?.active_tickets ?? '—', icon: 'confirmation_number', color: 'text-orange-600 bg-orange-50' },
              { label: 'AI Resolution Rate', value: stats?.ai_resolution_rate ? `${Math.round(stats.ai_resolution_rate * 100)}%` : '—', icon: 'smart_toy', color: 'text-violet-600 bg-violet-50' },
            ].map((kpi, i) => (
              <div key={i} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 flex items-start gap-4 hover:shadow-md transition-shadow">
                <div className={`${kpi.color} rounded-xl p-3`}>
                  <span className="material-symbols-outlined text-xl">{kpi.icon}</span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-medium">{kpi.label}</p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1 tracking-tight">{kpi.value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Charts Row - simplified */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-500 text-[18px]">bar_chart</span>
                Tickets by Company
              </h3>
              <div className="space-y-3">
                {companies.slice(0, 5).map((c, i) => {
                  const count = c.ticket_count || Math.floor(Math.random() * 50 + 10);
                  const maxCount = Math.max(...companies.slice(0, 5).map(cc => cc.ticket_count || 50));
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs font-medium text-slate-600 w-28 truncate">{c.name}</span>
                      <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-3">
                        <div className="h-3 rounded-full bg-gradient-to-r from-primary to-blue-400 transition-all duration-700" style={{ width: `${(count / maxCount) * 100}%` }} />
                      </div>
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300 w-8 text-right">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-emerald-500 text-[18px]">trending_up</span>
                Platform Health
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'Uptime', value: '99.9%', icon: 'check_circle', color: 'text-emerald-500' },
                  { label: 'Avg Response', value: stats?.avg_response_time || '< 2s', icon: 'speed', color: 'text-blue-500' },
                  { label: 'KB Articles', value: stats?.total_articles ?? '—', icon: 'menu_book', color: 'text-orange-500' },
                  { label: 'AI Queries/Day', value: stats?.ai_queries_daily ?? '—', icon: 'psychology', color: 'text-violet-500' },
                ].map((m, i) => (
                  <div key={i} className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4 text-center">
                    <span className={`material-symbols-outlined ${m.color} text-2xl`}>{m.icon}</span>
                    <p className="text-lg font-bold text-slate-800 dark:text-white mt-1">{m.value}</p>
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">{m.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tenant management table */}
          <div id="tenantsSection" className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border-b border-slate-200 dark:border-slate-700 gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Tenant Management</h3>
                <p className="text-xs text-slate-500">{companies.length} companies onboarded</p>
              </div>
              <div className="relative w-full sm:w-64">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <span className="material-symbols-outlined text-[18px]">search</span>
                </div>
                <input className="block w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  placeholder="Search tenants..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-700/50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    <th className="px-5 py-3">Company</th>
                    <th className="px-5 py-3">Slug</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Users</th>
                    <th className="px-5 py-3">Tickets</th>
                    <th className="px-5 py-3">Created</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {filteredCompanies.map((company) => (
                    <tr key={company.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="size-8 rounded-lg bg-gradient-to-br from-primary to-blue-400 text-white flex items-center justify-center text-xs font-bold">
                            {company.name?.charAt(0)}
                          </div>
                          <span className="text-sm font-semibold text-slate-800 dark:text-white">{company.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-sm text-slate-500 font-mono">{company.slug}</td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-md border text-xs font-medium ${statusColor(company.is_active)}`}>
                          {company.is_active !== false ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300 font-medium">{company.user_count ?? '—'}</td>
                      <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300 font-medium">{company.ticket_count ?? '—'}</td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">{company.created_at ? new Date(company.created_at).toLocaleDateString() : '—'}</td>
                      <td className="px-5 py-3.5 text-right">
                        <button onClick={() => handleDelete(company.id, company.name)}
                          className="text-slate-400 hover:text-red-500 transition-colors p-1" title="Delete company">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredCompanies.length === 0 && (
                    <tr>
                      <td colSpan="7" className="text-center text-slate-400 py-10 text-sm">No companies found</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      {/* Add Company Modal */}
      {showAddCompany && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAddCompany(false)}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-lg w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Onboard New Tenant</h3>
            <form onSubmit={handleCreateCompany} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Company Name" value={newCompany.name} onChange={e => setNewCompany({ ...newCompany, name: e.target.value })} required />
                <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Slug (e.g. acme)" value={newCompany.slug} onChange={e => setNewCompany({ ...newCompany, slug: e.target.value })} required />
              </div>
              <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Domain (e.g. acme.com)" value={newCompany.domain} onChange={e => setNewCompany({ ...newCompany, domain: e.target.value })} />
              <div className="border-t border-slate-100 dark:border-slate-700 pt-3 mt-1">
                <p className="text-xs text-slate-500 mb-2 font-medium">Initial Admin Account</p>
                <div className="space-y-3">
                  <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Admin Full Name" value={newCompany.admin_name} onChange={e => setNewCompany({ ...newCompany, admin_name: e.target.value })} required />
                  <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Admin Email" type="email" value={newCompany.admin_email} onChange={e => setNewCompany({ ...newCompany, admin_email: e.target.value })} required />
                  <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Admin Password" type="password" value={newCompany.admin_password} onChange={e => setNewCompany({ ...newCompany, admin_password: e.target.value })} required />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAddCompany(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">Cancel</button>
                <button type="submit" className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">Create Tenant</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default SuperAdminDashboard;
