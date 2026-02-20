import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

const SaasHelpdeskLogin = () => {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  if (isAuthenticated && user) {
    const paths = { super_admin: '/super-admin', company_admin: '/admin', it_staff: '/staff/tickets', employee: '/dashboard' };
    return <Navigate to={paths[user.role] || '/dashboard'} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { toast.error('Please enter email and password'); return; }
    setLoading(true);
    try {
      const userData = await login(email, password);
      toast.success(`Welcome back, ${userData.full_name}!`);
      const paths = { super_admin: '/super-admin', company_admin: '/admin', it_staff: '/staff/tickets', employee: '/dashboard' };
      navigate(paths[userData.role] || '/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="relative flex min-h-screen w-full flex-col justify-center overflow-hidden bg-background-light dark:bg-background-dark py-6 sm:py-12">
        <div className="absolute inset-0 bg-grid-pattern z-0 pointer-events-none"></div>
        <div className="absolute top-[-10%] left-[-10%] h-[500px] w-[500px] rounded-full bg-primary/5 blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-[-10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-primary/5 blur-[100px] pointer-events-none"></div>
        <div className="relative w-full max-w-md mx-auto px-4 z-10">
          <div className="flex flex-col items-center justify-center mb-8 gap-3">
            <div className="flex items-center justify-center h-12 w-12 rounded-xl bg-primary text-white shadow-lg shadow-primary/20">
              <span className="material-symbols-outlined text-3xl">smart_toy</span>
            </div>
            <h2 className="text-2xl font-bold text-primary dark:text-white tracking-tight">HelpDesk AI</h2>
          </div>
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-100 dark:border-slate-800 overflow-hidden">
            <div className="p-8">
              <div className="flex flex-col gap-2 mb-8 text-center">
                <h1 className="text-2xl font-bold text-primary dark:text-white tracking-tight">Welcome back</h1>
                <p className="text-slate-500 dark:text-slate-400 text-sm">Please enter your details to sign in to your tenant portal.</p>
              </div>
              <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-primary dark:text-slate-200 leading-none" htmlFor="email">Email</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400"><span className="material-symbols-outlined text-[20px]">mail</span></span>
                    <input className="flex h-12 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 pl-10 text-sm ring-offset-white placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 text-primary dark:text-white transition-all duration-200"
                      id="email" placeholder="name@company.com" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-primary dark:text-slate-200 leading-none" htmlFor="password">Password</label>
                    <a className="text-xs font-medium text-primary hover:text-primary/80 dark:text-slate-400 dark:hover:text-white hover:underline underline-offset-4" href="#">Forgot password?</a>
                  </div>
                  <div className="relative group">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400"><span className="material-symbols-outlined text-[20px]">lock</span></span>
                    <input className="flex h-12 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 pl-10 pr-10 text-sm ring-offset-white placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 text-primary dark:text-white transition-all duration-200"
                      id="password" placeholder="••••••••" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} />
                    <button className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-primary dark:hover:text-white transition-colors" type="button" onClick={() => setShowPassword(!showPassword)}>
                      <span className="material-symbols-outlined text-[20px]">{showPassword ? 'visibility' : 'visibility_off'}</span>
                    </button>
                  </div>
                </div>
                <button className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-bold ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-white hover:bg-primary/90 h-12 w-full mt-2 shadow-sm" type="submit" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-slate-200 dark:border-slate-700"></span></div>
                <div className="relative flex justify-center text-xs uppercase"><span className="bg-white dark:bg-slate-900 px-2 text-slate-500">Demo Accounts</span></div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => { setEmail('super@helpdesk.ai'); setPassword('super123'); }} className="text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg py-2 px-3 transition-colors text-slate-700 dark:text-slate-300">Super Admin</button>
                <button onClick={() => { setEmail('tom@acme.com'); setPassword('admin123'); }} className="text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg py-2 px-3 transition-colors text-slate-700 dark:text-slate-300">Company Admin</button>
                <button onClick={() => { setEmail('morgan@acme.com'); setPassword('staff123'); }} className="text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg py-2 px-3 transition-colors text-slate-700 dark:text-slate-300">IT Staff</button>
                <button onClick={() => { setEmail('alex@acme.com'); setPassword('employee123'); }} className="text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg py-2 px-3 transition-colors text-slate-700 dark:text-slate-300">Employee</button>
              </div>
            </div>
            <div className="px-8 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800">
              <p className="text-center text-sm text-slate-500 dark:text-slate-400">Don't have an account?{' '}<a className="font-semibold text-primary dark:text-white hover:underline" href="#">Contact Admin</a></p>
            </div>
          </div>
          <div className="mt-8 text-center"><p className="text-xs text-slate-400">© 2026 HelpDesk AI SaaS. Secure Login.</p></div>
        </div>
      </div>
    </div>
  );
};

export default SaasHelpdeskLogin;
