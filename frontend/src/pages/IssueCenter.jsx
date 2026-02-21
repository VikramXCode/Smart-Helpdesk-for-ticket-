import { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import { useAuth } from '../context/AuthContext';
import { addIssueMessage, createIssue, getIssue, listIssues } from '../api/issues';

const roleBadgeClass = {
  super_admin: 'bg-purple-100 text-purple-700',
  company_admin: 'bg-blue-100 text-blue-700',
};

const IssueCenter = () => {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'super_admin';

  const [issues, setIssues] = useState([]);
  const [selectedIssueId, setSelectedIssueId] = useState(null);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [issueForm, setIssueForm] = useState({ title: '', description: '' });
  const [creatingIssue, setCreatingIssue] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const selectedIssueMeta = useMemo(() => issues.find((i) => i.id === selectedIssueId), [issues, selectedIssueId]);
  const filteredIssues = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return issues.filter((issue) => {
      const matchesQuery = !query || issue.title?.toLowerCase().includes(query) || issue.company_name?.toLowerCase().includes(query);
      const matchesStatus = statusFilter === 'all' || issue.status === statusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [issues, searchQuery, statusFilter]);

  const totalMessages = useMemo(() => issues.reduce((sum, issue) => sum + (issue.message_count || 0), 0), [issues]);
  const openIssuesCount = useMemo(() => issues.filter((issue) => issue.status !== 'closed').length, [issues]);

  const loadIssues = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listIssues();
      const rows = res.data || [];
      setIssues(rows);
      if (!selectedIssueId && rows.length > 0) {
        setSelectedIssueId(rows[0].id);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  }, [selectedIssueId]);

  const loadIssueDetail = useCallback(async (issueId) => {
    if (!issueId) {
      setSelectedIssue(null);
      return;
    }
    try {
      const res = await getIssue(issueId);
      setSelectedIssue(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load issue details');
    }
  }, []);

  useEffect(() => { loadIssues(); }, [loadIssues]);
  useEffect(() => { loadIssueDetail(selectedIssueId); }, [selectedIssueId, loadIssueDetail]);

  const handleCreateIssue = async (e) => {
    e.preventDefault();
    if (!issueForm.title.trim() || !issueForm.description.trim()) return;

    try {
      setCreatingIssue(true);
      const res = await createIssue({
        title: issueForm.title,
        description: issueForm.description,
      });
      toast.success('Issue created');
      setIssueForm({ title: '', description: '' });
      await loadIssues();
      setSelectedIssueId(res.data.id);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create issue');
    } finally {
      setCreatingIssue(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedIssueId || !newMessage.trim()) return;
    try {
      setSending(true);
      await addIssueMessage(selectedIssueId, { content: newMessage.trim() });
      setNewMessage('');
      await loadIssueDetail(selectedIssueId);
      await loadIssues();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  return (
    <AdminLayout title={isSuperAdmin ? 'Issue Inbox' : 'Raise Issue'}>
      <div className="p-6 h-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Issues', value: issues.length, icon: 'bug_report', color: 'text-blue-600 bg-blue-50' },
            { label: 'Open Issues', value: openIssuesCount, icon: 'pending_actions', color: 'text-amber-600 bg-amber-50' },
            { label: 'Total Messages', value: totalMessages, icon: 'forum', color: 'text-violet-600 bg-violet-50' },
            { label: 'Selected Thread', value: selectedIssue ? `${(selectedIssue.messages || []).length} msgs` : '—', icon: 'chat', color: 'text-emerald-600 bg-emerald-50' },
          ].map((card) => (
            <div key={card.label} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 flex items-start gap-4">
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

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">
          <div className="lg:col-span-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-700 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">{isSuperAdmin ? 'Company Issues' : 'My Company Issues'}</h3>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm"
                  placeholder="Search issues..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select
                  className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            </div>
            <div className="max-h-[520px] overflow-y-auto">
              {loading ? (
                <div className="p-4 text-sm text-slate-500">Loading issues...</div>
              ) : filteredIssues.length === 0 ? (
                <div className="p-4 text-sm text-slate-500">No issues yet.</div>
              ) : filteredIssues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => setSelectedIssueId(issue.id)}
                  className={`w-full text-left px-4 py-3 border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/30 ${selectedIssueId === issue.id ? 'bg-slate-50 dark:bg-slate-700/30' : ''}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{issue.title}</p>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600">{issue.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 truncate">{issue.company_name || '—'}</p>
                  <p className="text-xs text-slate-400 mt-1">{issue.message_count || 0} messages</p>
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-8 grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2 flex flex-col gap-6">
            {!isSuperAdmin && (
              <form onSubmit={handleCreateIssue} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 space-y-3">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Create New Issue</h3>
                <input
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm"
                  placeholder="Issue title"
                  value={issueForm.title}
                  onChange={(e) => setIssueForm((prev) => ({ ...prev, title: e.target.value }))}
                />
                <textarea
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm"
                  rows={4}
                  placeholder="Describe your issue for super admin"
                  value={issueForm.description}
                  onChange={(e) => setIssueForm((prev) => ({ ...prev, description: e.target.value }))}
                />
                <button type="submit" disabled={creatingIssue} className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-slate-800 disabled:opacity-60">
                  {creatingIssue ? 'Submitting...' : 'Submit Issue'}
                </button>
              </form>
            )}

            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Issue Conversation</h3>
                {selectedIssueMeta && (
                  <p className="text-xs text-slate-500 mt-1">{selectedIssueMeta.title}</p>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[260px]">
                {!selectedIssue ? (
                  <p className="text-sm text-slate-500">Select an issue to view conversation.</p>
                ) : (selectedIssue.messages || []).length === 0 ? (
                  <p className="text-sm text-slate-500">No messages yet.</p>
                ) : (
                  (selectedIssue.messages || []).map((message) => (
                    <div key={message.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">{message.author_name}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded ${roleBadgeClass[message.author_role] || 'bg-slate-100 text-slate-600'}`}>{message.author_role.replace('_', ' ')}</span>
                        </div>
                        <span className="text-[10px] text-slate-400">{new Date(message.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-slate-700 dark:text-slate-300 mt-2 whitespace-pre-wrap">{message.content}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="p-4 border-t border-slate-200 dark:border-slate-700 flex gap-2">
                <input
                  className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm"
                  placeholder={selectedIssue ? 'Reply to this issue...' : 'Select an issue first'}
                  value={newMessage}
                  disabled={!selectedIssue}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!selectedIssue || sending || !newMessage.trim()}
                  className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-slate-800 disabled:opacity-60"
                >
                  {sending ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Issue Details</h3>
                {!selectedIssueMeta ? (
                  <p className="text-sm text-slate-500 mt-2">Select a thread to view details.</p>
                ) : (
                  <div className="mt-3 space-y-2 text-sm">
                    <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold">Title:</span> {selectedIssueMeta.title}</p>
                    <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold">Status:</span> {selectedIssueMeta.status}</p>
                    <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold">Company:</span> {selectedIssueMeta.company_name || '—'}</p>
                    <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold">Messages:</span> {selectedIssueMeta.message_count || 0}</p>
                  </div>
                )}
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Response Guidelines</h3>
                <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                  <p>• Keep updates actionable and specific.</p>
                  <p>• Include what was checked and next step.</p>
                  <p>• Mark resolved only after user confirmation.</p>
                  <p>• Use one thread per distinct incident.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default IssueCenter;
