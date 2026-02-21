import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AdminLayout } from '../components/AdminLayout';
import { createTicket, listTickets } from '../api/tickets';
import { getOverview } from '../api/analytics';
import { sendChat } from '../api/chat';
import toast from 'react-hot-toast';

const EmployeeDashboard = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ open: 0, resolved: 0, avgResolution: '—' });
  const [loading, setLoading] = useState(true);

  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [ticketRes, overviewRes] = await Promise.all([
        listTickets({ limit: 10, sort: 'created_at', order: 'desc' }),
        getOverview().catch(() => null),
      ]);
      setTickets(ticketRes.data.tickets || []);
      if (overviewRes?.data) {
        const d = overviewRes.data;
        const openCount = ticketRes.data.tickets?.filter(t => !['resolved', 'closed'].includes(t.status)).length || 0;
        const resolvedCount = ticketRes.data.tickets?.filter(t => ['resolved', 'closed'].includes(t.status)).length || 0;
        setStats({
          open: d.active_tickets ?? openCount,
          resolved: d.total_tickets_7d ?? resolvedCount,
          avgResolution: d.avg_resolution_time ? `${d.avg_resolution_time}h` : '—',
        });
      }
    } catch (err) {
      console.error('Failed to load data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) { toast.error('Please enter a ticket title'); return; }
    setSubmitting(true);
    try {
      const res = await createTicket({ title, description });
      toast.success(`Ticket ${res.data.ticket_number} created!`);
      setTitle(''); setDescription('');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChat = async () => {
    if (!chatMsg.trim()) return;
    const userMsg = chatMsg;
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatMsg('');
    setChatLoading(true);
    try {
      const res = await sendChat({
        message: userMsg,
        conversation_history: chatHistory.map(m => ({ role: m.role, content: m.content })),
      });
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: res.data.response,
        articles: Array.isArray(res.data.suggested_articles) ? res.data.suggested_articles : [],
      }]);
      if (res.data.ticket_created) {
        toast.success('AI created a ticket for you!');
        loadData();
      }
    } catch {
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const statusBadge = (status) => {
    const map = {
      new: 'bg-blue-100 text-blue-800 border-blue-200',
      open: 'bg-green-100 text-green-800 border-green-200',
      assigned: 'bg-sky-100 text-sky-800 border-sky-200',
      in_progress: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      pending: 'bg-amber-100 text-amber-800 border-amber-200',
      resolved: 'bg-green-100 text-green-800 border-green-200',
      closed: 'bg-slate-100 text-slate-600 border-slate-200',
      auto_resolved: 'bg-purple-100 text-purple-800 border-purple-200',
    };
    return map[status] || 'bg-slate-100 text-slate-600 border-slate-200';
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  const path = (location.pathname || '').toLowerCase();
  const activeView =
    path.endsWith('/open')
      ? 'open'
      : path.endsWith('/resolved')
        ? 'resolved'
        : 'all';

  const visibleTickets = tickets.filter((ticket) => {
    const status = (ticket.status || '').toLowerCase();
    if (activeView === 'open') return !['resolved', 'closed', 'auto_resolved'].includes(status);
    if (activeView === 'resolved') return ['resolved', 'closed', 'auto_resolved'].includes(status);
    return true;
  });

  const viewLabel = activeView === 'open' ? 'Open Tickets' : activeView === 'resolved' ? 'Resolved Tickets' : 'All Tickets';
  const viewDescription =
    activeView === 'open'
      ? 'Showing only active tickets that still need action.'
      : activeView === 'resolved'
        ? 'Showing only resolved or closed ticket history.'
        : "Here's what's happening with your support requests today.";

  const ticketMix = {
    open: tickets.filter((ticket) => ['new', 'open', 'assigned', 'in_progress', 'pending'].includes(ticket.status)).length,
    resolved: tickets.filter((ticket) => ['resolved', 'closed', 'auto_resolved'].includes(ticket.status)).length,
    highPriority: tickets.filter((ticket) => ['critical', 'high'].includes(ticket.priority)).length,
  };

  const topCategories = Object.entries(
    tickets.reduce((acc, ticket) => {
      const key = ticket.category || 'Uncategorized';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {})
  )
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <AdminLayout title="Dashboard">
      <main className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">{viewDescription}</p>
          <div className="mt-3 inline-flex items-center gap-2 text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
            <span className="material-symbols-outlined text-[14px]">dashboard</span>
            {viewLabel}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Submit ticket form */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            {activeView === 'all' ? (
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">Submit a New Ticket</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Describe your issue and our AI will triage it immediately.</p>
                </div>
                <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
                  <span className="material-symbols-outlined">auto_awesome</span>
                </div>
              </div>
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1" htmlFor="ticket-title">Ticket Title</label>
                  <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent py-2.5 px-4 placeholder-slate-400"
                    id="ticket-title" placeholder="e.g., VPN connection failed" type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1" htmlFor="ticket-desc">Description</label>
                  <textarea className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent py-3 px-4 placeholder-slate-400"
                    id="ticket-desc" placeholder="Please provide details about what happened..." rows="5" value={description} onChange={(e) => setDescription(e.target.value)} />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Priority</label>
                    <div className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300 py-2.5 px-4 text-sm">
                      Auto-assigned by AI
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Department</label>
                    <div className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300 py-2.5 px-4 text-sm">
                      Auto-classified by AI
                    </div>
                  </div>
                </div>
                <div className="pt-2 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <span className="material-symbols-outlined text-[18px] text-blue-500">info</span>
                    <span>AI will auto-classify and route your ticket.</span>
                  </div>
                  <button className="bg-primary hover:bg-slate-800 text-white font-medium py-2.5 px-6 rounded-lg transition-colors shadow-lg shadow-blue-900/20 flex items-center gap-2 disabled:opacity-50"
                    type="submit" disabled={submitting}>
                    <span>{submitting ? 'Submitting...' : 'Submit Request'}</span>
                    <span className="material-symbols-outlined text-[20px]">send</span>
                  </button>
                </div>
              </form>
            </div>
            ) : (
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">{activeView === 'open' ? 'Open Ticket Queue' : 'Resolved Ticket Archive'}</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {activeView === 'open'
                      ? 'Track active requests that still need action.'
                      : 'Review closed and resolved support history.'}
                  </p>
                </div>
                <span className="material-symbols-outlined text-blue-500">insights</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="rounded-lg bg-slate-50 dark:bg-slate-800 p-3 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-500">Visible Tickets</p>
                  <p className="text-xl font-bold text-slate-900 dark:text-white">{visibleTickets.length}</p>
                </div>
                <div className="rounded-lg bg-slate-50 dark:bg-slate-800 p-3 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-500">High Priority</p>
                  <p className="text-xl font-bold text-slate-900 dark:text-white">{ticketMix.highPriority}</p>
                </div>
                <div className="rounded-lg bg-slate-50 dark:bg-slate-800 p-3 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-500">Need New Ticket?</p>
                  <Link to="/dashboard" className="text-sm font-semibold text-blue-600 hover:text-blue-700">Go to Dashboard</Link>
                </div>
              </div>
            </div>
            )}

            {/* Stat cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden group">
                <div className="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-6xl text-blue-600">pending_actions</span>
                </div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Open Tickets</p>
                <div className="flex items-end gap-2">
                  <h3 className="text-3xl font-bold text-slate-900 dark:text-white">{loading ? '—' : stats.open}</h3>
                  <span className="text-xs font-medium text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400 px-1.5 py-0.5 rounded mb-1.5">Active</span>
                </div>
              </div>
              <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden group">
                <div className="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-6xl text-green-600">check_circle</span>
                </div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total (7 days)</p>
                <div className="flex items-end gap-2">
                  <h3 className="text-3xl font-bold text-slate-900 dark:text-white">{loading ? '—' : stats.resolved}</h3>
                  <span className="text-xs font-medium text-slate-500 mb-1.5">Last 7 days</span>
                </div>
              </div>
              <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden group">
                <div className="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-6xl text-purple-600">timer</span>
                </div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Avg Resolution</p>
                <div className="flex items-end gap-2">
                  <h3 className="text-3xl font-bold text-slate-900 dark:text-white">{loading ? '—' : stats.avgResolution}</h3>
                </div>
              </div>
            </div>
          </div>

          {/* Recent activity */}
          <div className="lg:col-span-5 flex flex-col h-full">
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col h-full max-h-[700px]">
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{viewLabel}</h2>
                <span className="text-xs px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">{visibleTickets.length} shown</span>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {loading ? (
                  <div className="flex items-center justify-center py-12 text-slate-400"><span className="material-symbols-outlined animate-spin mr-2">progress_activity</span> Loading...</div>
                ) : visibleTickets.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                    <span className="material-symbols-outlined text-4xl mb-2">inbox</span>
                    <p className="text-sm">No tickets yet. Submit your first one!</p>
                  </div>
                ) : visibleTickets.slice(0, 8).map((ticket) => {
                  const ticketIdentifier = ticket.id || ticket.ticket_id;
                  const cardClasses = `p-4 rounded-lg transition-colors group border block ${
                    ticketIdentifier
                      ? 'hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer border-transparent hover:border-slate-200 dark:hover:border-slate-700'
                      : 'opacity-70 cursor-not-allowed border-slate-100 dark:border-slate-800'
                  }`;

                  if (!ticketIdentifier) {
                    return (
                      <div key={`${ticket.ticket_number || ticket.title}-missing-id`} className={cardClasses}>
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-slate-400">{ticket.ticket_number}</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusBadge(ticket.status)}`}>
                              {ticket.status?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          </div>
                          <span className="text-xs text-slate-400">{timeAgo(ticket.created_at)}</span>
                        </div>
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">{ticket.title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          {ticket.priority && (
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                              ticket.priority === 'critical' ? 'bg-red-100 text-red-700' :
                              ticket.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                              ticket.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-slate-100 text-slate-600'
                            }`}>{ticket.priority}</span>
                          )}
                          {ticket.category && <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{ticket.category}</span>}
                        </div>
                      </div>
                    );
                  }

                  return (
                  <Link to={`/tickets/${ticketIdentifier}`} key={ticketIdentifier}
                    className={cardClasses}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">{ticket.ticket_number}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusBadge(ticket.status)}`}>
                          {ticket.status?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </div>
                      <span className="text-xs text-slate-400">{timeAgo(ticket.created_at)}</span>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1 group-hover:text-blue-600 transition-colors">{ticket.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {ticket.priority && (
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                          ticket.priority === 'critical' ? 'bg-red-100 text-red-700' :
                          ticket.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                          ticket.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>{ticket.priority}</span>
                      )}
                      {ticket.category && <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{ticket.category}</span>}
                    </div>
                  </Link>
                );})}
              </div>
              <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 rounded-b-xl">
                <div className="flex items-center gap-3 text-sm text-slate-500">
                  <span className="material-symbols-outlined text-[20px] text-orange-500">lightbulb</span>
                  <p>Click any ticket to view details and conversation.</p>
                </div>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6">
              <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">My Ticket Health</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Open / Active', value: ticketMix.open, color: 'bg-blue-500' },
                    { label: 'Resolved / Closed', value: ticketMix.resolved, color: 'bg-emerald-500' },
                    { label: 'High Priority', value: ticketMix.highPriority, color: 'bg-orange-500' },
                  ].map((item) => {
                    const totalCount = Math.max(1, tickets.length);
                    const width = (item.value / totalCount) * 100;
                    return (
                      <div key={item.label}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-slate-600 dark:text-slate-300">{item.label}</span>
                          <span className="font-semibold text-slate-800 dark:text-white">{item.value}</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-700">
                          <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${width}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                  <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">Top Categories</p>
                  {topCategories.length === 0 ? (
                    <p className="text-sm text-slate-500">No ticket categories yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {topCategories.map(([name, count]) => (
                        <div key={name} className="flex items-center justify-between text-sm">
                          <span className="text-slate-700 dark:text-slate-300 truncate">{name}</span>
                          <span className="font-semibold text-slate-900 dark:text-white">{count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Quick Actions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    onClick={() => document.getElementById('ticket-title')?.focus()}
                    className="text-left rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">Create Ticket</p>
                    <p className="text-xs text-slate-500 mt-1">Jump to form and submit quickly.</p>
                  </button>
                  <Link
                    to="/staff/tickets"
                    className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">Track Queue</p>
                    <p className="text-xs text-slate-500 mt-1">Open full ticket tracking view.</p>
                  </Link>
                  <button
                    onClick={() => setChatOpen(true)}
                    className="text-left rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">Ask AI Assistant</p>
                    <p className="text-xs text-slate-500 mt-1">Get guidance or auto-create tickets.</p>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* AI Chat FAB + Panel */}
      <div className="fixed bottom-6 right-6 z-40">
        {chatOpen && (
          <div className="absolute bottom-16 right-0 w-80 sm:w-96 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 flex flex-col max-h-[500px] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 bg-primary text-white rounded-t-2xl">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined">smart_toy</span>
                <span className="font-semibold text-sm">HelpDesk AI Assistant</span>
              </div>
              <button onClick={() => setChatOpen(false)} className="hover:bg-white/20 rounded p-1 transition-colors">
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px]">
              {chatHistory.length === 0 && (
                <div className="text-center text-sm text-slate-400 py-8">
                  <span className="material-symbols-outlined text-3xl mb-2 block">chat</span>
                  Ask me anything about IT support!
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === 'user' ? 'bg-primary text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
                  }`}>
                    <div>{msg.content}</div>
                    {msg.role === 'assistant' && Array.isArray(msg.articles) && msg.articles.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {msg.articles.map((article) => (
                          <div key={article.id} className="rounded-lg border border-slate-200 dark:border-slate-600 p-2 bg-white/80 dark:bg-slate-800/60">
                            <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">{article.title}</div>
                            <div className="text-[11px] text-slate-500 truncate">{article.summary}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {chatLoading && <div className="flex justify-start"><div className="bg-slate-100 dark:bg-slate-700 rounded-xl px-3 py-2 text-sm text-slate-500 animate-pulse">Thinking...</div></div>}
            </div>
            <div className="p-3 border-t border-slate-200 dark:border-slate-700 flex gap-2">
              <input className="flex-1 text-sm border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-700 text-slate-800 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="Type a message..." value={chatMsg} onChange={(e) => setChatMsg(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleChat()} />
              <button onClick={handleChat} disabled={chatLoading} className="bg-primary text-white px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50">
                <span className="material-symbols-outlined text-[18px]">send</span>
              </button>
            </div>
          </div>
        )}
        <button onClick={() => setChatOpen(!chatOpen)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-xl shadow-blue-600/30 transition-all hover:scale-105 flex items-center justify-center group relative">
          <span className="material-symbols-outlined text-3xl">{chatOpen ? 'close' : 'smart_toy'}</span>
          <span className="absolute right-0 top-0 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-sky-500"></span>
          </span>
        </button>
      </div>
    </AdminLayout>
  );
};

export default EmployeeDashboard;
