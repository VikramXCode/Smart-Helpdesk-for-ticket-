import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listArticles, createArticle } from '../api/knowledge';
import toast from 'react-hot-toast';

const KnowledgeBaseGrid = () => {
  const { user, logout } = useAuth();
  const [articles, setArticles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [showAdd, setShowAdd] = useState(false);
  const [newArticle, setNewArticle] = useState({ title: '', content: '', category: '' });

  const categories = ['Hardware', 'Software', 'Network', 'Security', 'HR Policy', 'Access'];
  const isStaff = ['it_staff', 'company_admin', 'super_admin'].includes(user?.role);

  useEffect(() => { loadArticles(); }, [search, category, page]);

  const loadArticles = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 12 };
      if (search) params.search = search;
      if (category) params.category = category;
      const res = await listArticles(params);
      setArticles(res.data.articles || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createArticle(newArticle);
      toast.success('Article created!');
      setShowAdd(false);
      setNewArticle({ title: '', content: '', category: '' });
      loadArticles();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create article');
    }
  };

  const categoryColor = (cat) => {
    const map = {
      Network: 'bg-blue-50 text-blue-700 border-blue-100',
      Hardware: 'bg-purple-50 text-purple-700 border-purple-100',
      Software: 'bg-orange-50 text-orange-700 border-orange-100',
      Security: 'bg-green-50 text-green-700 border-green-100',
      'HR Policy': 'bg-pink-50 text-pink-700 border-pink-100',
      Access: 'bg-sky-50 text-sky-700 border-sky-100',
    };
    return map[cat] || 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const hoverColor = (cat) => {
    const map = {
      Network: 'group-hover:text-blue-600',
      Hardware: 'group-hover:text-purple-600',
      Software: 'group-hover:text-orange-600',
      Security: 'group-hover:text-green-600',
      'HR Policy': 'group-hover:text-pink-600',
      Access: 'group-hover:text-sky-600',
    };
    return map[cat] || 'group-hover:text-blue-600';
  };

  const totalPages = Math.ceil(total / 12);

  return (
    <div className="w-full min-h-screen bg-background-light dark:bg-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-4 sm:px-10 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4 text-primary dark:text-white">
            <div className="size-8 rounded bg-primary text-white flex items-center justify-center">
              <span className="material-symbols-outlined">smart_toy</span>
            </div>
            <h2 className="text-lg font-bold leading-tight tracking-tight">HelpDesk AI</h2>
          </div>
          <nav className="hidden md:flex flex-1 justify-center gap-8">
            <Link to="/dashboard" className="text-slate-500 hover:text-primary text-sm font-medium transition-colors">Home</Link>
            <Link to={isStaff ? '/staff/tickets' : '/dashboard'} className="text-slate-500 hover:text-primary text-sm font-medium transition-colors">Tickets</Link>
            <Link to="/knowledge" className="text-primary dark:text-white text-sm font-bold transition-colors">Knowledge Base</Link>
          </nav>
          <div className="flex items-center gap-4">
            {isStaff && (
              <button onClick={() => setShowAdd(true)} className="hidden sm:flex items-center justify-center rounded-lg h-9 px-4 bg-primary hover:bg-primary/90 text-white text-sm font-bold transition-colors shadow-sm">
                <span>New Article</span>
              </button>
            )}
            <div className="flex items-center gap-2 cursor-pointer" onClick={logout}>
              <div className="size-9 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold">{user?.full_name?.charAt(0)}</div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center w-full">
        {/* Hero search */}
        <div className="w-full bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 pb-12 pt-10 px-4">
          <div className="max-w-4xl mx-auto text-center flex flex-col items-center gap-6">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-primary dark:text-white">How can we help you today?</h1>
            <p className="text-slate-500 dark:text-slate-400 text-lg max-w-2xl">Search for troubleshooting guides, error codes, policy documents, and more.</p>
            <div className="w-full max-w-2xl mt-4 relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-primary transition-colors">
                <span className="material-symbols-outlined">search</span>
              </div>
              <input className="block w-full pl-12 pr-4 py-4 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-primary dark:text-white placeholder-slate-400 focus:ring-4 focus:ring-primary/10 focus:border-primary transition-all shadow-sm text-base"
                placeholder="Search for articles (e.g., 'VPN setup', 'Reset password')..."
                type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
            </div>
            <div className="flex flex-wrap justify-center gap-3 mt-4">
              <button onClick={() => { setCategory(''); setPage(1); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${!category ? 'bg-primary text-white shadow-sm ring-1 ring-primary/20' : 'bg-white dark:bg-slate-800 hover:bg-slate-50 text-slate-500 border border-slate-200 dark:border-slate-700'}`}>
                {!category && <span className="material-symbols-outlined text-[18px]">check</span>} All
              </button>
              {categories.map(cat => (
                <button key={cat} onClick={() => { setCategory(cat === category ? '' : cat); setPage(1); }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${category === cat ? 'bg-primary text-white shadow-sm' : 'bg-white dark:bg-slate-800 hover:bg-slate-50 text-slate-500 border border-slate-200 dark:border-slate-700'}`}>
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Articles grid */}
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-primary dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary dark:text-white">auto_awesome</span>
              {search ? `Results for "${search}"` : 'Popular Articles'}
            </h3>
            <span className="text-sm text-slate-500">{total} articles</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              <span className="material-symbols-outlined animate-spin text-2xl mr-2">progress_activity</span> Loading articles...
            </div>
          ) : articles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <span className="material-symbols-outlined text-5xl mb-3">article</span>
              <p className="text-lg font-medium">No articles found</p>
              <p className="text-sm mt-1">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article) => (
                <article key={article.id} className="group bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer flex flex-col h-full">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${categoryColor(article.category)}`}>
                      {article.category || 'General'}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">visibility</span> {article.view_count || 0}
                    </span>
                  </div>
                  <h4 className={`text-lg font-bold text-primary dark:text-white mb-2 ${hoverColor(article.category)} transition-colors`}>{article.title}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 line-clamp-2 flex-1">
                    {article.content?.substring(0, 150)}...
                  </p>
                  <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-700 mt-auto">
                    <div className="flex items-center gap-2">
                      <div className="size-6 rounded-full bg-primary text-white flex items-center justify-center text-[10px] font-bold">
                        {article.author_name?.charAt(0) || 'A'}
                      </div>
                      <span className="text-xs font-medium text-slate-500">{article.author_name || 'Admin'}</span>
                    </div>
                    <span className="text-xs text-slate-400">
                      {article.updated_at ? `Updated ${new Date(article.updated_at).toLocaleDateString()}` : ''}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-8 gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors">Previous</button>
              <span className="px-4 py-2 text-sm text-slate-600">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors">Next</button>
            </div>
          )}
        </div>
      </main>

      {/* Add Article FAB (mobile) */}
      {isStaff && (
        <button onClick={() => setShowAdd(true)} className="lg:hidden fixed bottom-6 right-6 bg-primary text-white rounded-full p-4 shadow-xl z-40 hover:bg-slate-800 transition-colors">
          <span className="material-symbols-outlined text-2xl">add</span>
        </button>
      )}

      {/* Add Article Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAdd(false)}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-lg w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">New Knowledge Article</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <input className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Article Title" value={newArticle.title} onChange={e => setNewArticle({ ...newArticle, title: e.target.value })} required />
              <select className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" value={newArticle.category} onChange={e => setNewArticle({ ...newArticle, category: e.target.value })}>
                <option value="">Select Category</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <textarea className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white" placeholder="Article content..." rows="8" value={newArticle.content} onChange={e => setNewArticle({ ...newArticle, content: e.target.value })} required />
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAdd(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">Cancel</button>
                <button type="submit" className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">Publish Article</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseGrid;
