import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import { getStats, listCompanies } from '../api/superadmin';

const SuperAdminPlatformMetrics = () => {
  const [stats, setStats] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [statsRes, companiesRes] = await Promise.all([getStats(), listCompanies({ limit: 100 })]);
        setStats(statsRes.data);
        setCompanies(companiesRes.data.companies || []);
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Failed to load platform metrics');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const totalTickets = companies.reduce((sum, c) => sum + (c.total_tickets || 0), 0);
  const totalUsers = companies.reduce((sum, c) => sum + (c.total_users || 0), 0);
  const activeTenants = companies.filter((company) => company.is_active !== false).length;
  const avgTicketsPerTenant = companies.length ? Math.round((stats?.processed_tickets ?? totalTickets) / companies.length) : 0;
  const avgUsersPerTenant = companies.length ? Math.round((stats?.total_users ?? totalUsers) / companies.length) : 0;

  const cards = [
    { label: 'Total Companies', value: stats?.total_companies ?? companies.length, icon: 'apartment', color: 'text-blue-600 bg-blue-50' },
    { label: 'Total Users', value: stats?.total_users ?? totalUsers, icon: 'group', color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Processed Tickets', value: stats?.processed_tickets ?? totalTickets, icon: 'confirmation_number', color: 'text-orange-600 bg-orange-50' },
    { label: 'AI Resolution Rate', value: stats?.ai_resolution_rate != null ? `${Math.round(stats.ai_resolution_rate)}%` : '0%', icon: 'smart_toy', color: 'text-violet-600 bg-violet-50' },
  ];

  const topCompanies = [...companies]
    .sort((a, b) => ((b.total_tickets || b.ticket_count || 0) - (a.total_tickets || a.ticket_count || 0)))
    .slice(0, 8);

  const maxTopTickets = Math.max(1, ...topCompanies.map((c) => c.total_tickets || c.ticket_count || 0));

  return (
    <AdminLayout title="Platform Metrics">
      <div className="p-6 space-y-6">
        {loading ? (
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-8 text-sm text-slate-500">
            Loading metrics...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {cards.map((card) => (
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

            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Top Tenants by Ticket Volume</h3>
              {topCompanies.length === 0 ? (
                <p className="text-sm text-slate-500">No tenant data available.</p>
              ) : (
                <div className="space-y-3">
                  {topCompanies.map((company) => {
                    const ticketCount = company.total_tickets || company.ticket_count || 0;
                    return (
                      <div key={company.id} className="flex items-center gap-3">
                        <span className="text-sm text-slate-700 dark:text-slate-300 w-56 truncate">{company.name}</span>
                        <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-3">
                          <div className="h-3 rounded-full bg-gradient-to-r from-primary to-blue-400" style={{ width: `${(ticketCount / maxTopTickets) * 100}%` }} />
                        </div>
                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300 w-12 text-right">{ticketCount}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Capacity & Health Snapshot</h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Active Tenants', value: activeTenants, icon: 'domain_verification', color: 'text-emerald-500' },
                    { label: 'Inactive Tenants', value: Math.max(0, companies.length - activeTenants), icon: 'error', color: 'text-rose-500' },
                    { label: 'Avg Tickets / Tenant', value: avgTicketsPerTenant, icon: 'insights', color: 'text-blue-500' },
                    { label: 'Avg Users / Tenant', value: avgUsersPerTenant, icon: 'groups', color: 'text-violet-500' },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-4">
                      <span className={`material-symbols-outlined ${metric.color} text-xl`}>{metric.icon}</span>
                      <p className="text-xl font-bold text-slate-800 dark:text-white mt-1">{metric.value}</p>
                      <p className="text-[11px] uppercase tracking-wider text-slate-500 mt-0.5">{metric.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Tenant Activity Feed</h3>
                {topCompanies.length === 0 ? (
                  <p className="text-sm text-slate-500">No activity available yet.</p>
                ) : (
                  <div className="space-y-3">
                    {topCompanies.slice(0, 6).map((company, index) => (
                      <div key={company.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-800 dark:text-white truncate">{company.name}</p>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">Top {index + 1}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          {company.ticket_count || company.total_tickets || 0} tickets · {company.user_count || company.total_users || 0} users
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="p-5 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Tenant Leaderboard</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-700/50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      <th className="px-5 py-3">Tenant</th>
                      <th className="px-5 py-3">Users</th>
                      <th className="px-5 py-3">Tickets</th>
                      <th className="px-5 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {topCompanies.length === 0 ? (
                      <tr>
                        <td colSpan="4" className="px-5 py-8 text-center text-sm text-slate-500">No leaderboard data yet.</td>
                      </tr>
                    ) : (
                      topCompanies.map((company) => (
                        <tr key={company.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                          <td className="px-5 py-3.5 text-sm font-semibold text-slate-800 dark:text-white">{company.name}</td>
                          <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300">{company.user_count || company.total_users || 0}</td>
                          <td className="px-5 py-3.5 text-sm text-slate-600 dark:text-slate-300">{company.ticket_count || company.total_tickets || 0}</td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex px-2.5 py-0.5 rounded-md border text-xs font-medium ${company.is_active !== false ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                              {company.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default SuperAdminPlatformMetrics;
