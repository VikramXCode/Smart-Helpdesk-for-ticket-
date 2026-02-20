import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createTicket, listTickets } from '../api/tickets';
import { getOverview } from '../api/analytics';
import { sendChat } from '../api/chat';
import toast from 'react-hot-toast';

const EmployeeDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [department, setDepartment] = useState('IT Support');
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
      const res = await createTicket({ title, description, priority, department });
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
      setChatHistory(prev => [...prev, { role: 'assistant', content: res.data.response }]);
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

  return (
    <div className="w-full min-h-screen bg-background-light dark:bg-slate-900">
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-primary dark:text-white">
                <div className="size-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                  <span className="material-symbols-outlined">smart_toy</span>
                </div>
                <h2 className="text-xl font-bold tracking-tight">HelpDesk AI</h2>
              </div>
              <nav className="hidden md:flex ml-8 gap-6 text-sm font-medium text-slate-500 dark:text-slate-400">
                <Link to="/dashboard" className="text-slate-900 dark:text-white hover:text-blue-600 transition-colors">Dashboard</Link>
                <Link to="/knowledge" className="hover:text-blue-600 transition-colors">Knowledge Base</Link>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center relative">
                <span className="absolute left-3 text-slate-400"><span className="material-symbols-outlined text-[20px]">search</span></span>
                <input className="pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-sm w-64 focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="Search knowledge base..." type="text" />
              </div>
              <div className="flex items-center gap-2 cursor-pointer" onClick={logout}>
                <div className="size-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <span className="hidden sm:inline text-sm font-medium text-slate-700 dark:text-slate-300">{user?.full_name}</span>
                <span className="material-symbols-outlined text-slate-400 text-[18px]">logout</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Here's what's happening with your support requests today.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Submit ticket form */}
          <div className="lg:col-span-7 flex flex-col gap-6">
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
                    <select className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 py-2.5 px-4"
                      value={priority} onChange={(e) => setPriority(e.target.value)}>
                      <option value="low">Low - General Question</option>
                      <option value="medium">Medium - Affects Productivity</option>
                      <option value="high">High - System Down</option>
                      <option value="critical">Critical - Business Impact</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Department</label>
                    <select className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 py-2.5 px-4"
                      value={department} onChange={(e) => setDepartment(e.target.value)}>
                      <option>IT Support</option>
                      <option>HR</option>
                      <option>Facilities</option>
                      <option>Legal</option>
                    </select>
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
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Activity</h2>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {loading ? (
                  <div className="flex items-center justify-center py-12 text-slate-400"><span className="material-symbols-outlined animate-spin mr-2">progress_activity</span> Loading...</div>
                ) : tickets.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                    <span className="material-symbols-outlined text-4xl mb-2">inbox</span>
                    <p className="text-sm">No tickets yet. Submit your first one!</p>
                  </div>
                ) : tickets.slice(0, 8).map((ticket) => (
                  <Link to={`/tickets/${ticket.id}`} key={ticket.id}
                    className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg transition-colors cursor-pointer group border border-transparent hover:border-slate-200 dark:hover:border-slate-700 block">
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
                ))}
              </div>
              <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 rounded-b-xl">
                <div className="flex items-center gap-3 text-sm text-slate-500">
                  <span className="material-symbols-outlined text-[20px] text-orange-500">lightbulb</span>
                  <p>Click any ticket to view details and conversation.</p>
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
                  <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === 'user' ? 'bg-primary text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
                  }`}>{msg.content}</div>
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
    </div>
  );
};

export default EmployeeDashboard;
