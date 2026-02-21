import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import { createCompany, listCompanies } from '../api/superadmin';

const SLUG_REGEX = /^[a-z0-9-]{2,100}$/;

const emptyForm = {
  name: '',
  slug: '',
  domain: '',
  admin_name: '',
  admin_email: '',
  admin_password: '12345678',
};

const SuperAdminOnboardTenant = () => {
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [recentCompanies, setRecentCompanies] = useState([]);
  const [loadingRecent, setLoadingRecent] = useState(true);

  const completionScore =
    [form.name, form.slug, form.admin_name, form.admin_email, form.admin_password].filter(Boolean).length * 20;

  const loadRecent = async () => {
    setLoadingRecent(true);
    try {
      const res = await listCompanies({ limit: 5, offset: 0 });
      setRecentCompanies((res.data.companies || []).slice(0, 5));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load recent tenants');
    } finally {
      setLoadingRecent(false);
    }
  };

  useEffect(() => {
    loadRecent();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const normalizedSlug = (form.slug || '')
      .toLowerCase()
      .trim()
      .replace(/[_\s]+/g, '-')
      .replace(/[^a-z0-9-]/g, '');

    if (!SLUG_REGEX.test(normalizedSlug)) {
      toast.error('Slug must be 2-100 chars: lowercase letters, numbers, and hyphens only');
      return;
    }

    if ((form.admin_name || '').trim().length < 2) {
      toast.error('Admin name must be at least 2 characters');
      return;
    }

    setSubmitting(true);
    try {
      await createCompany({
        name: (form.name || '').trim(),
        slug: normalizedSlug,
        admin_name: (form.admin_name || '').trim(),
        admin_email: (form.admin_email || '').trim(),
        admin_password: form.admin_password,
      });
      toast.success('Tenant onboarded successfully');
      setForm(emptyForm);
      loadRecent();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to onboard tenant');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AdminLayout title="Onboard Tenant">
      <div className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">Create New Tenant Workspace</h3>
          <p className="text-sm text-slate-500 mb-5">Set up tenant profile and bootstrap the initial company admin account.</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Tenant Details</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white"
                  placeholder="Company Name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
                <input
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white"
                  placeholder="Slug (e.g. novaworks)"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  required
                />
              </div>
              <input
                className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white mt-3"
                placeholder="Domain (optional, e.g. novaworks.com)"
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
              />
            </div>

            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">Initial Company Admin</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white"
                  placeholder="Admin Full Name"
                  value={form.admin_name}
                  onChange={(e) => setForm({ ...form, admin_name: e.target.value })}
                  required
                />
                <input
                  type="email"
                  className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white"
                  placeholder="Admin Email"
                  value={form.admin_email}
                  onChange={(e) => setForm({ ...form, admin_email: e.target.value })}
                  required
                />
              </div>
              <input
                type="password"
                className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5 dark:text-white mt-3"
                placeholder="Initial Password"
                value={form.admin_password}
                onChange={(e) => setForm({ ...form, admin_password: e.target.value })}
                required
              />
              <p className="text-xs text-slate-500 mt-2">Default is <span className="font-semibold">12345678</span>, and the admin must change it on first login.</p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                className="px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
                onClick={() => setForm(emptyForm)}
                disabled={submitting}
              >
                Reset
              </button>
              <button
                type="submit"
                className="px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-60"
                disabled={submitting}
              >
                {submitting ? 'Creating...' : 'Create Tenant'}
              </button>
            </div>
          </form>

          <div className="mt-6 rounded-xl border border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-900/50">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Form Completion</p>
              <p className="text-xs font-bold text-slate-700 dark:text-slate-300">{completionScore}%</p>
            </div>
            <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700">
              <div className="h-2 rounded-full bg-gradient-to-r from-primary to-blue-400" style={{ width: `${completionScore}%` }} />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Onboarding Checklist</h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">Recommended rollout steps for each new tenant.</p>
            <div className="space-y-2">
              {[
                'Create company profile and unique slug',
                'Create initial company admin account',
                'Admin logs in and resets default password',
                'Configure categories and team mappings',
                'Validate ticket intake and AI routing',
              ].map((item) => (
                <div key={item} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <span className="material-symbols-outlined text-emerald-500 text-[18px] mt-0.5">check_circle</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Recent Tenants</h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">Quick view of the latest onboarded organizations.</p>
            {loadingRecent ? (
              <p className="text-sm text-slate-500">Loading recent tenants...</p>
            ) : recentCompanies.length === 0 ? (
              <p className="text-sm text-slate-500">No tenants found yet.</p>
            ) : (
              <div className="space-y-3">
                {recentCompanies.map((company) => (
                  <div key={company.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{company.name}</p>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono">{company.slug || '—'}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{company.domain || 'No domain set'}</p>
                    <p className="text-[11px] text-slate-400 mt-2">Created {company.created_at ? new Date(company.created_at).toLocaleDateString() : '—'}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Policy Guardrails</h3>
            <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300 mt-3">
              <p>• Slug must be unique across all tenants.</p>
              <p>• Initial admin password should remain temporary.</p>
              <p>• Tenant activation depends on first successful admin login.</p>
              <p>• Category-team routing should be configured before go-live.</p>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default SuperAdminOnboardTenant;
