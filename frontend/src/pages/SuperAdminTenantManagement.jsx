import { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import { listCompanies, deleteCompany } from '../api/superadmin';

const statusColor = (active) =>
  active !== false
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : 'bg-red-50 text-red-700 border-red-200';

const SuperAdminTenantManagement = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const loadCompanies = async () => {
    setLoading(true);
    try {
      const res = await listCompanies({ limit: 100 });
      setCompanies(res.data.companies || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete ${name}? This is irreversible.`)) return;
    try {
      await deleteCompany(id);
      toast.success(`${name} deleted`);
      loadCompanies();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete tenant');
    }
  };

  const filteredCompanies = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return companies;
    return companies.filter(
      (company) =>
        company.name?.toLowerCase().includes(query) ||
        company.slug?.toLowerCase().includes(query) ||
        company.domain?.toLowerCase().includes(query)
    );
  }, [companies, searchQuery]);

  const totals = useMemo(() => {
    const active = companies.filter((c) => c.is_active !== false).length;
    const users = companies.reduce((sum, c) => sum + (c.user_count || 0), 0);
    const tickets = companies.reduce((sum, c) => sum + (c.ticket_count || 0), 0);
    return {
      tenants: companies.length,
      active,
      users,
      tickets,
    };
  }, [companies]);

  const topByTickets = useMemo(
    () => [...companies].sort((a, b) => (b.ticket_count || 0) - (a.ticket_count || 0)).slice(0, 5),
    [companies]
  );

  const latestTenants = useMemo(
    () => [...companies].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).slice(0, 5),
    [companies]
  );

  return (
    <AdminLayout title="Tenant Management">
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Tenants', value: totals.tenants, icon: 'apartment', color: 'text-blue-600 bg-blue-50' },
            { label: 'Active Tenants', value: totals.active, icon: 'check_circle', color: 'text-emerald-600 bg-emerald-50' },
            { label: 'Users Across Tenants', value: totals.users, icon: 'group', color: 'text-violet-600 bg-violet-50' },
            { label: 'Tickets Across Tenants', value: totals.tickets, icon: 'confirmation_number', color: 'text-orange-600 bg-orange-50' },
          ].map((card) => (
            <div key={card.label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 flex items-start gap-4">
              <div className={`${card.color} rounded-xl p-3`}>
                <span className="material-symbols-outlined text-xl">{card.icon}</span>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">{card.label}</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1 tracking-tight">{card.value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border-b border-slate-200 dark:border-slate-700 gap-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">All Tenants</h3>
              <p className="text-xs text-slate-500">Search, review, and remove tenant organizations</p>
            </div>
            <div className="relative w-full sm:w-72">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <span className="material-symbols-outlined text-[18px]">search</span>
              </div>
              <input
                className="block w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary"
                placeholder="Search by name, slug, domain..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="px-5 py-3">Company</th>
                  <th className="px-5 py-3">Slug</th>
                  <th className="px-5 py-3">Domain</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Users</th>
                  <th className="px-5 py-3">Tickets</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan="8" className="text-center text-slate-400 py-10 text-sm">Loading tenants...</td>
                  </tr>
                ) : filteredCompanies.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="text-center text-slate-400 py-10 text-sm">No tenants found</td>
                  </tr>
                ) : (
                  filteredCompanies.map((company) => (
                    <tr key={company.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="size-8 rounded-lg bg-gradient-to-br from-primary to-blue-400 text-white flex items-center justify-center text-xs font-bold">
                            {company.name?.charAt(0) || '?'}
                          </div>
                          <span className="text-sm font-semibold text-slate-800 dark:text-white">{company.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-sm text-slate-500 font-mono">{company.slug || '—'}</td>
                      <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300">{company.domain || '—'}</td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-md border text-xs font-medium ${statusColor(company.is_active)}`}>
                          {company.is_active !== false ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300 font-medium">{company.user_count ?? '—'}</td>
                      <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300 font-medium">{company.ticket_count ?? '—'}</td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">{company.created_at ? new Date(company.created_at).toLocaleDateString() : '—'}</td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => handleDelete(company.id, company.name)}
                          className="text-slate-400 hover:text-red-500 transition-colors p-1"
                          title="Delete tenant"
                        >
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Top Tenants by Ticket Volume</h3>
            {topByTickets.length === 0 ? (
              <p className="text-sm text-slate-500">No tenant activity yet.</p>
            ) : (
              <div className="space-y-3">
                {topByTickets.map((company) => {
                  const max = Math.max(1, ...topByTickets.map((c) => c.ticket_count || 0));
                  const count = company.ticket_count || 0;
                  return (
                    <div key={company.id} className="flex items-center gap-3">
                      <span className="text-sm text-slate-700 dark:text-slate-300 w-44 truncate">{company.name}</span>
                      <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-3">
                        <div className="h-3 rounded-full bg-gradient-to-r from-primary to-blue-400" style={{ width: `${(count / max) * 100}%` }} />
                      </div>
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300 w-10 text-right">{count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Newest Onboarded Tenants</h3>
            {latestTenants.length === 0 ? (
              <p className="text-sm text-slate-500">No recent onboarding data yet.</p>
            ) : (
              <div className="space-y-3">
                {latestTenants.map((company) => (
                  <div key={company.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{company.name}</p>
                      <span className={`inline-flex px-2 py-0.5 rounded text-[11px] border ${statusColor(company.is_active)}`}>
                        {company.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{company.domain || 'No domain configured'}</p>
                    <p className="text-[11px] text-slate-400 mt-1">Created {company.created_at ? new Date(company.created_at).toLocaleDateString() : '—'}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default SuperAdminTenantManagement;
