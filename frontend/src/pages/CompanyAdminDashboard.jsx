import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AdminLayout } from '../components/AdminLayout';
import { getOverview, getVolume, getCategories } from '../api/analytics';
import { listAgents, createAgent, listTeams, createTeam, updateTeam, deleteTeam } from '../api/admin';
import { changePassword } from '../api/auth';
import toast from 'react-hot-toast';

const CompanyAdminDashboard = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [volume, setVolume] = useState(null);
  const [categories, setCategories] = useState(null);
  const [agents, setAgents] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [volumePeriod, setVolumePeriod] = useState('7d');
  const [activeTab, setActiveTab] = useState('team');

  // Add Agent modal
  const [showAddAgent, setShowAddAgent] = useState(false);
  const [newAgent, setNewAgent] = useState({ email: '', full_name: '', role: 'it_staff', department: '' });

  // Add Team modal
  const [showAddTeam, setShowAddTeam] = useState(false);
  const [newTeam, setNewTeam] = useState({ name: '', description: '', email: '' });
  const [editingTeamId, setEditingTeamId] = useState(null);
  const [showForcePasswordModal, setShowForcePasswordModal] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' });

  useEffect(() => { loadData(); }, []);
  useEffect(() => { getVolume(volumePeriod).then(r => setVolume(r.data)).catch(() => {}); }, [volumePeriod]);
  useEffect(() => {
    if (user?.role === 'company_admin' && user?.password_change_required) {
      setShowForcePasswordModal(true);
      setPasswordForm((prev) => ({ ...prev, current: prev.current || '12345678' }));
    }
  }, [user]);

  const loadData = async () => {
    try {
      const [overviewRes, volumeRes, catRes, agentRes, teamRes] = await Promise.all([
        getOverview().catch(() => ({ data: {} })),
        getVolume('7d').catch(() => ({ data: { labels: [], values: [] } })),
        getCategories().catch(() => ({ data: { total: 0, categories: [] } })),
        listAgents({ limit: 50 }).catch(() => ({ data: { agents: [] } })),
        listTeams().catch(() => ({ data: [] })),
      ]);
      setOverview(overviewRes.data);
      setVolume(volumeRes.data);
      setCategories(catRes.data);
      setAgents(agentRes.data.agents || []);
      setTeams(teamRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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

  const handleAddAgent = async (e) => {
    e.preventDefault();
    try {
      await createAgent(newAgent);
      toast.success('Agent added successfully');
      setShowAddAgent(false);
      setNewAgent({ email: '', full_name: '', role: 'it_staff', department: '' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add agent');
    }
  };

  const handleAddTeam = async (e) => {
    e.preventDefault();
    try {
      if (editingTeamId) {
        await updateTeam(editingTeamId, newTeam);
        toast.success('Team updated successfully');
      } else {
        await createTeam(newTeam);
        toast.success('Team created successfully');
      }
      setShowAddTeam(false);
      setNewTeam({ name: '', description: '', email: '' });
      setEditingTeamId(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save team');
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (!window.confirm('Are you sure you want to delete this team?')) return;
    try {
      await deleteTeam(teamId);
      toast.success('Team deleted successfully');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete team');
    }
  };

  const openEditTeam = (team) => {
    setEditingTeamId(team.id);
    setNewTeam({ name: team.name, description: team.description || '', email: team.email || '' });
    setShowAddTeam(true);
  };

  // Build SVG chart path from volume data
  const buildChartPath = () => {
    if (!volume?.values?.length) return { path: '', fill: '', points: [] };
    const vals = volume.values;
    const max = Math.max(...vals, 1);
    const w = 750, h = 180;
    const step = vals.length > 1 ? w / (vals.length - 1) : w;
    const pts = vals.map((v, i) => ({ x: i * step, y: h - (v / max) * h }));
    let d = `M${pts[0].x},${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const cx = (pts[i - 1].x + pts[i].x) / 2;
      d += ` C${cx},${pts[i - 1].y} ${cx},${pts[i].y} ${pts[i].x},${pts[i].y}`;
    }
    const fillD = d + ` L${pts[pts.length - 1].x},200 L${pts[0].x},200 Z`;
    return { path: d, fill: fillD, points: pts };
  };

  const chart = buildChartPath();

  // Category donut
  const donutSegments = () => {
    if (!categories?.categories?.length) return [];
    const colors = ['#3b82f6', '#8b5cf6', '#0ea5e9', '#94a3b8', '#f59e0b', '#ef4444'];
    const total = categories.total || categories.categories.reduce((s, c) => s + c.count, 0);
    const circumference = 2 * Math.PI * 40;
    let offset = 0;
    return categories.categories.map((cat, i) => {
      const pct = total > 0 ? cat.count / total : 0;
      const len = pct * circumference;
      const seg = { ...cat, color: colors[i % colors.length], dasharray: `${len} ${circumference}`, dashoffset: -offset };
      offset += len + 5;
      return seg;
    });
  };

  const statusColor = (s) => {
    if (s === 'online') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    if (s === 'away') return 'bg-amber-100 text-amber-800 border-amber-200';
    return 'bg-slate-100 text-slate-600 border-slate-200';
  };

  const statusDot = (s) => s === 'online' ? 'bg-emerald-500' : s === 'away' ? 'bg-amber-500' : 'bg-slate-500';

  const o = overview || {};
  const onlineAgents = agents.filter((agent) => agent.status === 'online').length;
  const awayAgents = agents.filter((agent) => agent.status === 'away').length;
  const offlineAgents = Math.max(0, agents.length - onlineAgents - awayAgents);
  const headerAction = (
    <button onClick={() => navigate('/staff/tickets')} className="flex items-center gap-2 bg-primary hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm">
      <span className="material-symbols-outlined text-[20px]">confirmation_number</span><span>View Tickets</span>
    </button>
  );

  return (
    <div className="w-full">
      <AdminLayout title="Company Overview" headerAction={headerAction}>
        <div className="p-8">
          <div className="max-w-7xl mx-auto flex flex-col gap-8">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-2 rounded-lg text-accent"><span className="material-symbols-outlined">verified</span></div>
                    {o.sla_compliance != null && <span className="flex items-center text-emerald-600 text-sm font-medium bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full"><span className="material-symbols-outlined text-[16px] mr-1">trending_up</span>SLA</span>}
                  </div>
                  <div><p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">SLA Compliance</p><h3 className="text-3xl font-bold text-primary dark:text-white tracking-tight">{loading ? '—' : `${o.sla_compliance ?? 0}%`}</h3></div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-purple-50 dark:bg-purple-900/20 p-2 rounded-lg text-purple-600"><span className="material-symbols-outlined">timer</span></div>
                  </div>
                  <div><p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Avg Resolution Time</p><h3 className="text-3xl font-bold text-primary dark:text-white tracking-tight">{loading ? '—' : `${o.avg_resolution_time ?? 0}h`}</h3></div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-amber-50 dark:bg-amber-900/20 p-2 rounded-lg text-amber-600"><span className="material-symbols-outlined">confirmation_number</span></div>
                  </div>
                  <div><p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Active Tickets</p><h3 className="text-3xl font-bold text-primary dark:text-white tracking-tight">{loading ? '—' : o.active_tickets ?? 0}</h3></div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-rose-50 dark:bg-rose-900/20 p-2 rounded-lg text-rose-600"><span className="material-symbols-outlined">auto_awesome</span></div>
                  </div>
                  <div><p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">AI Resolution Rate</p><h3 className="text-3xl font-bold text-primary dark:text-white tracking-tight">{loading ? '—' : `${o.ai_resolution_rate ?? 0}%`}</h3></div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
                  <h3 className="text-lg font-bold text-primary dark:text-white mb-1">Operations Snapshot</h3>
                  <p className="text-sm text-slate-500 mb-5">Current staffing and routing readiness across your support operation.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                    {[
                      { label: 'Total Agents', value: agents.length, icon: 'support_agent', color: 'text-blue-600 bg-blue-50' },
                      { label: 'Online Now', value: onlineAgents, icon: 'wifi', color: 'text-emerald-600 bg-emerald-50' },
                      { label: 'Teams Configured', value: teams.length, icon: 'groups', color: 'text-violet-600 bg-violet-50' },
                      { label: 'Categories (from Teams)', value: teams.length, icon: 'alt_route', color: 'text-orange-600 bg-orange-50' },
                    ].map((item) => (
                      <div key={item.label} className="rounded-lg border border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-900/50">
                        <div className="flex items-center justify-between">
                          <span className={`material-symbols-outlined ${item.color} rounded-lg p-2`}>{item.icon}</span>
                          <span className="text-xl font-bold text-slate-900 dark:text-white">{item.value}</span>
                        </div>
                        <p className="text-xs uppercase tracking-wider text-slate-500 mt-3">{item.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
                  <h3 className="text-lg font-bold text-primary dark:text-white mb-1">Agent Presence</h3>
                  <p className="text-sm text-slate-500 mb-5">Live team availability at a glance.</p>
                  <div className="space-y-3">
                    {[
                      { label: 'Online', value: onlineAgents, bar: 'bg-emerald-500' },
                      { label: 'Away', value: awayAgents, bar: 'bg-amber-500' },
                      { label: 'Offline', value: offlineAgents, bar: 'bg-slate-500' },
                    ].map((row) => {
                      const width = agents.length ? (row.value / agents.length) * 100 : 0;
                      return (
                        <div key={row.label}>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-slate-600 dark:text-slate-300">{row.label}</span>
                            <span className="font-semibold text-slate-800 dark:text-white">{row.value}</span>
                          </div>
                          <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-700">
                            <div className={`h-2 rounded-full ${row.bar}`} style={{ width: `${width}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Charts row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Ticket Volume chart */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-bold text-primary dark:text-white">Ticket Volume</h3>
                      <p className="text-sm text-slate-500">Inbound tickets over the period</p>
                    </div>
                    <select className="bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg p-2 dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                      value={volumePeriod} onChange={(e) => setVolumePeriod(e.target.value)}>
                      <option value="7d">Last 7 Days</option>
                      <option value="30d">Last 30 Days</option>
                    </select>
                  </div>
                  <div className="relative h-64 w-full">
                    {volume?.values?.length > 0 ? (
                      <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 750 200">
                        <defs>
                          <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <path d={chart.fill} fill="url(#chartGradient)" />
                        <path d={chart.path} fill="none" stroke="#3b82f6" strokeLinecap="round" strokeWidth="3" vectorEffect="non-scaling-stroke" />
                        {chart.points.map((p, i) => (
                          <circle key={i} className="fill-white stroke-blue-500 stroke-2" cx={p.x} cy={p.y} r="4" />
                        ))}
                      </svg>
                    ) : (
                      <div className="flex items-center justify-center h-full text-slate-400 text-sm">No data available</div>
                    )}
                  </div>
                  {volume?.labels && (
                    <div className="flex justify-between px-2 mt-2 text-xs font-medium text-slate-400">
                      {volume.labels.map((l, i) => <span key={i}>{l}</span>)}
                    </div>
                  )}
                </div>

                {/* Category donut */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 flex flex-col">
                  <h3 className="text-lg font-bold text-primary dark:text-white mb-1">Ticket Categories</h3>
                  <p className="text-sm text-slate-500 mb-6">Distribution by issue type</p>
                  <div className="flex-1 flex flex-col items-center justify-center">
                    <div className="relative size-48">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" fill="none" r="40" stroke="#e2e8f0" strokeWidth="12" />
                        {donutSegments().map((seg, i) => (
                          <circle key={i} cx="50" cy="50" fill="none" r="40" stroke={seg.color} strokeDasharray={seg.dasharray} strokeDashoffset={seg.dashoffset} strokeWidth="12" className="transition-all cursor-pointer hover:opacity-80" />
                        ))}
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center flex-col">
                        <span className="text-3xl font-bold text-primary dark:text-white">{categories?.total || 0}</span>
                        <span className="text-xs text-slate-500 font-medium">Total</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 space-y-3">
                    {donutSegments().map((seg, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span className="size-3 rounded-full" style={{ backgroundColor: seg.color }}></span>
                          <span className="text-slate-600 dark:text-slate-300">{seg.label || seg.category}</span>
                        </div>
                        <span className="font-bold text-slate-900 dark:text-white">{seg.percentage ?? Math.round(seg.count / (categories?.total || 1) * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Team management */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <div className="border-b border-slate-200 dark:border-slate-700 px-6 pt-4 flex gap-6">
                  <button onClick={() => setActiveTab('team')} className={`pb-4 px-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'team' ? 'text-accent border-accent' : 'text-slate-500 border-transparent hover:text-slate-700'}`}>Team Management</button>
                  <button onClick={() => setActiveTab('teams')} className={`pb-4 px-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'teams' ? 'text-accent border-accent' : 'text-slate-500 border-transparent hover:text-slate-700'}`}>Teams</button>
                </div>

                <div className="p-6">
                  {activeTab === 'team' && (
                    <>
                      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                        <h3 className="text-lg font-bold text-primary dark:text-white">Helpdesk Agents</h3>
                        <button onClick={() => setShowAddAgent(true)} className="flex items-center gap-2 bg-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm">
                          <span className="material-symbols-outlined text-[20px]">person_add</span><span>Add Agent</span>
                        </button>
                      </div>
                      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-500 uppercase font-medium text-xs">
                            <tr>
                              <th className="px-6 py-3">Agent</th>
                              <th className="px-6 py-3">Role</th>
                              <th className="px-6 py-3">Status</th>
                              <th className="px-6 py-3">Department</th>
                              <th className="px-6 py-3">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                            {agents.length === 0 && (
                              <tr><td colSpan="5" className="px-6 py-8 text-center text-slate-400">No agents found</td></tr>
                            )}
                            {agents.map((agent) => (
                              <tr key={agent.id} className="bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-slate-900 dark:text-white whitespace-nowrap">
                                  <div className="flex items-center gap-3">
                                    <div className="size-8 rounded-full bg-accent text-white flex items-center justify-center text-xs font-bold">{agent.full_name?.charAt(0)}</div>
                                    <div>
                                      <div className="font-semibold">{agent.full_name}</div>
                                      <div className="text-xs text-slate-500">{agent.email}</div>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{agent.role?.replace('_', ' ')}</td>
                                <td className="px-6 py-4">
                                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${statusColor(agent.status)}`}>
                                    <span className={`size-1.5 rounded-full ${statusDot(agent.status)}`}></span>
                                    {agent.status || 'offline'}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{agent.department || '—'}</td>
                                <td className="px-6 py-4"><button className="text-slate-400 hover:text-slate-600"><span className="material-symbols-outlined text-[20px]">more_vert</span></button></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                  {activeTab === 'teams' && (
                    <>
                      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                        <h3 className="text-lg font-bold text-primary dark:text-white">Helpdesk Teams</h3>
                        <button onClick={() => { setEditingTeamId(null); setNewTeam({ name: '', description: '', email: '' }); setShowAddTeam(true); }} className="flex items-center gap-2 bg-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm">
                          <span className="material-symbols-outlined text-[20px]">group_add</span><span>Add Team</span>
                        </button>
                      </div>
                      {teams.length === 0 ? (
                        <p className="text-slate-400 text-sm text-center py-8">No teams configured yet. Create one to get started.</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {teams.map(t => (
                            <div key={t.id} className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:shadow-md transition-shadow">
                              <div className="flex justify-between items-start mb-3">
                                <div className="flex-1">
                                  <h4 className="font-semibold text-slate-900 dark:text-white">{t.name}</h4>
                                  {t.description && <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{t.description}</p>}
                                  {t.email && <p className="text-xs text-slate-500 mt-2">{t.email}</p>}
                                  <p className="text-xs text-slate-400 mt-2">Members: <span className="font-semibold">{t.member_count || 0}</span></p>
                                </div>
                                <div className="flex gap-2">
                                  <button onClick={() => openEditTeam(t)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-400">
                                    <span className="material-symbols-outlined text-[20px]">edit</span>
                                  </button>
                                  <button onClick={() => handleDeleteTeam(t.id)} className="p-2 hover:bg-red-100 dark:hover:bg-red-900/20 rounded text-red-600">
                                    <span className="material-symbols-outlined text-[20px]">delete</span>
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
      </AdminLayout>

      {/* Add Agent Modal */}
      {showAddAgent && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAddAgent(false)}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Add New Agent</h3>
            <form onSubmit={handleAddAgent} className="space-y-4">
              <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5" placeholder="Full Name" value={newAgent.full_name} onChange={e => setNewAgent({...newAgent, full_name: e.target.value})} required />
              <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5" placeholder="Email" type="email" value={newAgent.email} onChange={e => setNewAgent({...newAgent, email: e.target.value})} required />
              <div className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-sm px-4 py-2.5 text-slate-500 dark:text-slate-300">
                Default password: 12345678 (agent must change on first login)
              </div>
              <select className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5" value={newAgent.role} onChange={e => setNewAgent({...newAgent, role: e.target.value})}>
                <option value="it_staff">IT Staff</option>
              </select>
              <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5" placeholder="Department (optional)" value={newAgent.department} onChange={e => setNewAgent({...newAgent, department: e.target.value})} />
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAddAgent(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">Cancel</button>
                <button type="submit" className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">Add Agent</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add/Edit Team Modal */}
      {showAddTeam && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => { setShowAddTeam(false); setEditingTeamId(null); }}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">{editingTeamId ? 'Edit Team' : 'Create New Team'}</h3>
            <form onSubmit={handleAddTeam} className="space-y-4">
              <input className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 text-slate-900 dark:text-white" placeholder="Team Name" value={newTeam.name} onChange={e => setNewTeam({...newTeam, name: e.target.value})} required />
              <textarea className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 text-slate-900 dark:text-white" placeholder="Team Description (what does this team handle?)" value={newTeam.description} onChange={e => setNewTeam({...newTeam, description: e.target.value})} rows="3" />
              <input className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 text-slate-900 dark:text-white" placeholder="Team Email (optional)" type="email" value={newTeam.email} onChange={e => setNewTeam({...newTeam, email: e.target.value})} />
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowAddTeam(false); setEditingTeamId(null); }} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors dark:text-white">Cancel</button>
                <button type="submit" className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">{editingTeamId ? 'Update Team' : 'Create Team'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showForcePasswordModal && (
        <div className="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Change Default Password</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">For security, you must change the default company admin password before continuing.</p>
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
    </div>
  );
};

export default CompanyAdminDashboard;
