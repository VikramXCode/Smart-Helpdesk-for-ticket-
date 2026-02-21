import { useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import { bulkCreateEmployees, createEmployee } from '../api/admin';

const CompanyAdminEmployeeImport = () => {
  const [emails, setEmails] = useState([]);
  const [fileName, setFileName] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [singleForm, setSingleForm] = useState({ email: '', full_name: '' });
  const [singleSubmitting, setSingleSubmitting] = useState(false);

  const previewEmails = useMemo(() => emails.slice(0, 10), [emails]);

  const parseCsv = async (file) => {
    const text = await file.text();
    const lines = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);

    if (!lines.length) {
      throw new Error('CSV is empty');
    }

    const header = lines[0].split(',').map((h) => h.trim().toLowerCase());
    const mailsIndex = header.findIndex((h) => h === 'mails');
    if (mailsIndex === -1) {
      throw new Error('CSV must contain a column named mails');
    }

    const parsed = [];
    for (let i = 1; i < lines.length; i += 1) {
      const cols = lines[i].split(',');
      const value = (cols[mailsIndex] || '').trim();
      if (value) parsed.push(value);
    }

    return parsed;
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const parsedEmails = await parseCsv(file);
      if (!parsedEmails.length) {
        toast.error('No emails found in mails column');
        setEmails([]);
        setFileName(file.name);
        return;
      }

      setEmails(parsedEmails);
      setFileName(file.name);
      setResult(null);
      toast.success(`Loaded ${parsedEmails.length} email(s) from CSV`);
    } catch (err) {
      toast.error(err.message || 'Failed to parse CSV');
      setEmails([]);
      setFileName(file.name);
      setResult(null);
    }
  };

  const handleImport = async () => {
    if (!emails.length) {
      toast.error('Upload a CSV with mails column first');
      return;
    }

    setProcessing(true);
    try {
      const res = await bulkCreateEmployees(emails);
      setResult(res.data);
      toast.success(`Created ${res.data.created_count} employee account(s)`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create employees');
    } finally {
      setProcessing(false);
    }
  };

  const handleCreateOne = async (e) => {
    e.preventDefault();
    if (!singleForm.email.trim()) {
      toast.error('Email is required');
      return;
    }

    setSingleSubmitting(true);
    try {
      const payload = {
        email: singleForm.email.trim(),
      };
      if (singleForm.full_name.trim()) payload.full_name = singleForm.full_name.trim();

      await createEmployee(payload);
      toast.success('Employee account created with default password 12345678');
      setSingleForm({ email: '', full_name: '' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create employee');
    } finally {
      setSingleSubmitting(false);
    }
  };

  return (
    <AdminLayout title="Employee Onboarding">
      <div className="p-6 space-y-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Create One Employee</h3>
          <p className="text-sm text-slate-500 mt-1">
            Create a single employee account with default password <span className="font-semibold">12345678</span> (must be changed on first login).
          </p>

          <form onSubmit={handleCreateOne} className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <div className="md:col-span-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">Email</label>
              <input
                type="email"
                value={singleForm.email}
                onChange={(e) => setSingleForm((prev) => ({ ...prev, email: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-3 py-2"
                placeholder="employee@company.com"
                required
              />
            </div>
            <div className="md:col-span-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">Full Name (optional)</label>
              <input
                type="text"
                value={singleForm.full_name}
                onChange={(e) => setSingleForm((prev) => ({ ...prev, full_name: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-3 py-2"
                placeholder="Jane Doe"
              />
            </div>
            <button
              type="submit"
              disabled={singleSubmitting}
              className="h-10 px-4 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-60"
            >
              {singleSubmitting ? 'Creating...' : 'Create Employee'}
            </button>
          </form>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Bulk Create Employees from CSV</h3>
          <p className="text-sm text-slate-500 mt-1">
            Upload a CSV containing one column named <span className="font-semibold">mails</span>. New employees get default password <span className="font-semibold">12345678</span> and must change it on first login.
          </p>

          <div className="mt-5 space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-2">CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
              {fileName && <p className="text-xs text-slate-500 mt-2">Loaded file: {fileName}</p>}
            </div>

            <button
              onClick={handleImport}
              disabled={processing || !emails.length}
              className="px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-60"
            >
              {processing ? 'Importing...' : 'Create Employee Accounts'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Email Preview</h3>
            {!emails.length ? (
              <p className="text-sm text-slate-500">No emails loaded yet.</p>
            ) : (
              <>
                <p className="text-xs text-slate-500 mb-3">Total loaded: {emails.length}</p>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {previewEmails.map((email) => (
                    <div key={email} className="text-sm text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700 px-3 py-2">
                      {email}
                    </div>
                  ))}
                </div>
                {emails.length > 10 && <p className="text-xs text-slate-400 mt-2">...and {emails.length - 10} more</p>}
              </>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Import Result</h3>
            {!result ? (
              <p className="text-sm text-slate-500">Run import to see created and skipped emails.</p>
            ) : (
              <div className="space-y-4">
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                  <p className="text-sm font-semibold text-emerald-700">Created: {result.created_count}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">Skipped Emails (duplicates/existing/invalid)</p>
                  {!result.skipped_emails?.length ? (
                    <p className="text-sm text-slate-500">No skipped emails.</p>
                  ) : (
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {result.skipped_emails.map((email) => (
                        <div key={email} className="text-sm text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700 px-3 py-2">
                          {email}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default CompanyAdminEmployeeImport;
