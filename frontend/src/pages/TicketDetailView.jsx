import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTicket, addMessage, updateTicket, resolveTicket, getAiSuggestion, getSimilarArticles } from '../api/tickets';
import toast from 'react-hot-toast';

const TicketDetailView = () => {
  const { ticketId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [similarArticles, setSimilarArticles] = useState([]);
  const [status, setStatus] = useState('');

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  const loadTicket = async () => {
    setLoading(true);
    try {
      const res = await getTicket(ticketId);
      const t = res.data;
      setTicket(t);
      setMessages(t.messages || []);
      setStatus(t.status);

      // Load AI suggestion and similar articles in parallel
      const [aiRes, artRes] = await Promise.all([
        getAiSuggestion(ticketId).catch(() => null),
        getSimilarArticles(ticketId).catch(() => null),
      ]);
      if (aiRes?.data) setAiSuggestion(aiRes.data);
      if (artRes?.data) setSimilarArticles(artRes.data);
    } catch (err) {
      toast.error('Failed to load ticket');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async () => {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const res = await addMessage(ticketId, { content: reply });
      setMessages(prev => [...prev, res.data]);
      setReply('');
      toast.success('Reply sent');
    } catch (err) {
      toast.error('Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      if (newStatus === 'resolved') {
        await resolveTicket(ticketId);
      } else {
        await updateTicket(ticketId, { status: newStatus });
      }
      setStatus(newStatus);
      setTicket(prev => ({ ...prev, status: newStatus }));
      toast.success(`Status updated to ${newStatus.replace('_', ' ')}`);
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const priorityColors = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    low: 'bg-slate-100 text-slate-600 border-slate-200',
  };

  const statusColors = {
    new: 'bg-blue-100 text-blue-800',
    assigned: 'bg-sky-100 text-sky-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    pending: 'bg-amber-100 text-amber-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-slate-100 text-slate-600',
    auto_resolved: 'bg-purple-100 text-purple-800',
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background-light">
        <div className="flex flex-col items-center gap-3">
          <span className="material-symbols-outlined text-3xl text-primary animate-spin">progress_activity</span>
          <p className="text-slate-500 text-sm">Loading ticket...</p>
        </div>
      </div>
    );
  }

  if (!ticket) return null;

  const isStaff = ['it_staff', 'company_admin', 'super_admin'].includes(user?.role);

  return (
    <div className="w-full min-h-screen bg-background-light dark:bg-slate-900">
      {/* Top nav */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate(-1)} className="p-1 text-slate-500 hover:text-primary transition-colors">
                <span className="material-symbols-outlined">arrow_back</span>
              </button>
              <div className="flex items-center gap-2 text-primary dark:text-white">
                <div className="size-7 bg-primary rounded flex items-center justify-center text-white">
                  <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                </div>
                <h2 className="text-lg font-bold tracking-tight">HelpDesk AI</h2>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isStaff && (
                <select className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white dark:bg-slate-700 dark:border-slate-600 dark:text-white focus:ring-2 focus:ring-primary"
                  value={status} onChange={(e) => handleStatusChange(e.target.value)}>
                  <option value="new">New</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="pending">Pending</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              )}
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status] || statusColors.new}`}>
                {ticket.status?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <div className="flex items-center text-sm text-slate-500 mb-6">
          <Link to={isStaff ? '/staff/tickets' : '/dashboard'} className="hover:text-primary transition-colors">
            {isStaff ? 'Tickets' : 'Dashboard'}
          </Link>
          <span className="mx-2">/</span>
          <span className="text-primary font-medium dark:text-white">{ticket.ticket_number}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Ticket header */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-xl font-bold text-slate-900 dark:text-white">{ticket.title}</h1>
                  <div className="flex items-center gap-3 mt-2 text-sm text-slate-500">
                    <span>{ticket.ticket_number}</span>
                    <span>•</span>
                    <span>Created {timeAgo(ticket.created_at)}</span>
                    {ticket.source && <><span>•</span><span>via {ticket.source}</span></>}
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${priorityColors[ticket.priority] || priorityColors.medium}`}>
                  {ticket.priority?.charAt(0).toUpperCase() + ticket.priority?.slice(1)}
                </span>
              </div>
              {ticket.description && (
                <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{ticket.description}</p>
              )}
            </div>

            {/* Conversation thread */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Conversation</h3>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {messages.length === 0 ? (
                  <div className="p-8 text-center text-slate-400">
                    <span className="material-symbols-outlined text-3xl mb-2">forum</span>
                    <p className="text-sm">No messages yet. Start the conversation below.</p>
                  </div>
                ) : messages.map((msg) => (
                  <div key={msg.id} className={`p-6 ${msg.author_type === 'ai' ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}`}>
                    <div className="flex items-start gap-3">
                      <div className={`size-9 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold text-white ${
                        msg.author_type === 'ai' ? 'bg-blue-600' :
                        msg.author_type === 'agent' ? 'bg-emerald-600' : 'bg-slate-400'
                      }`}>
                        {msg.author_type === 'ai' ? (
                          <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                        ) : (
                          msg.author_name?.charAt(0) || 'U'
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-slate-900 dark:text-white">
                            {msg.author_type === 'ai' ? 'HelpDesk AI' : msg.author_name || 'User'}
                          </span>
                          {msg.author_type === 'ai' && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-700 border border-blue-200">AI Response</span>
                          )}
                          {msg.is_internal && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-700 border border-amber-200">Internal</span>
                          )}
                          <span className="text-xs text-slate-400">{timeAgo(msg.created_at)}</span>
                        </div>
                        <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Reply box */}
              <div className="border-t border-slate-200 dark:border-slate-700 p-6">
                <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <textarea className="w-full p-4 text-sm bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border-none focus:ring-0 resize-none placeholder-slate-400"
                    placeholder="Type your reply..." rows="4" value={reply} onChange={(e) => setReply(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleReply(); }} />
                  <div className="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700">
                    <div className="flex gap-2">
                      <button className="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-200 dark:hover:bg-slate-700"><span className="material-symbols-outlined text-[20px]">image</span></button>
                      <button className="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-200 dark:hover:bg-slate-700"><span className="material-symbols-outlined text-[20px]">attach_file</span></button>
                    </div>
                    <button onClick={handleReply} disabled={sending || !reply.trim()}
                      className="bg-primary hover:bg-slate-800 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50">
                      <span>{sending ? 'Sending...' : 'Send Reply'}</span>
                      <span className="material-symbols-outlined text-[18px]">send</span>
                    </button>
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-2">Press Ctrl+Enter to send</p>
              </div>
            </div>
          </div>

          {/* Right sidebar */}
          <div className="flex flex-col gap-6">
            {/* Ticket details */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-4">Ticket Details</h3>
              <div className="space-y-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Priority</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium border ${priorityColors[ticket.priority] || priorityColors.medium}`}>
                    {ticket.priority?.charAt(0).toUpperCase() + ticket.priority?.slice(1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Category</span>
                  <span className="font-medium text-slate-900 dark:text-white">{ticket.category || 'Uncategorized'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Source</span>
                  <span className="font-medium text-slate-900 dark:text-white">{ticket.source || 'web'}</span>
                </div>
                {ticket.assigned_team && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Team</span>
                    <span className="font-medium text-slate-900 dark:text-white">{ticket.assigned_team}</span>
                  </div>
                )}
                {ticket.assigned_to_name && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Assigned To</span>
                    <span className="font-medium text-slate-900 dark:text-white">{ticket.assigned_to_name}</span>
                  </div>
                )}
                {ticket.due_date && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Due Date</span>
                    <span className="font-medium text-slate-900 dark:text-white">{new Date(ticket.due_date).toLocaleDateString()}</span>
                  </div>
                )}
                {ticket.department && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Department</span>
                    <span className="font-medium text-slate-900 dark:text-white">{ticket.department}</span>
                  </div>
                )}
              </div>
            </div>

            {/* People */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-6">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-4">People</h3>
              <div className="space-y-3">
                {ticket.created_by_name && (
                  <div className="flex items-center gap-3">
                    <div className="size-8 rounded-full bg-slate-400 text-white flex items-center justify-center text-xs font-bold">{ticket.created_by_name.charAt(0)}</div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">{ticket.created_by_name}</p>
                      <p className="text-xs text-slate-500">Reporter</p>
                    </div>
                  </div>
                )}
                {ticket.assigned_to_name && (
                  <div className="flex items-center gap-3">
                    <div className="size-8 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">{ticket.assigned_to_name.charAt(0)}</div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">{ticket.assigned_to_name}</p>
                      <p className="text-xs text-slate-500">Assignee</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Suggestion */}
            {(aiSuggestion?.text || ticket.ai_suggestion) && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-3">
                  <span className="material-symbols-outlined text-blue-600">auto_awesome</span>
                  <h3 className="text-base font-bold text-blue-900 dark:text-blue-200">AI Suggestion</h3>
                </div>
                <p className="text-sm text-blue-800 dark:text-blue-300 leading-relaxed">
                  {aiSuggestion?.text || ticket.ai_suggestion}
                </p>
                {aiSuggestion?.confidence != null && (
                  <div className="mt-3 flex items-center gap-2">
                    <div className="flex-1 bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
                      <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${aiSuggestion.confidence * 100}%` }}></div>
                    </div>
                    <span className="text-xs text-blue-600 font-medium">{Math.round(aiSuggestion.confidence * 100)}% confidence</span>
                  </div>
                )}
              </div>
            )}

            {/* End of sections */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketDetailView;
