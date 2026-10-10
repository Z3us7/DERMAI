import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, Settings as SettingsIcon, Sun, Moon, UserCircle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import About from './pages/About';
import Library from './pages/Library';
import Settings from './pages/Settings';
import Auth from './pages/Auth';
import Background3D from './components/Background3D';

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/about" element={<About />} />
        <Route path="/library" element={<Library />} />

        {/* Protected routes — require login */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/scan" element={<ProtectedRoute><Scanner /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      </Routes>
    </AnimatePresence>
  );
}

function AppContent() {
  const [isDark, setIsDark] = useState(() => {
    // Persist dark mode preference
    return localStorage.getItem('dermai-dark-mode') === 'true';
  });
  const { user, profile } = useAuth();

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('dermai-dark-mode', isDark);
  }, [isDark]);

  return (
    <>
      <Background3D isDark={isDark} />
      <div className="flex flex-col min-h-screen">
        {/* Navigation Bar */}
        <nav className="glass-nav sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link to="/" className="flex items-center gap-2 text-amber-700 dark:text-amber-400 font-bold text-xl tracking-tight mr-4">
                <Activity strokeWidth={2.5} /> DermAI
              </Link>
              <div className="hidden md:flex gap-1">
                <Link to="/about" className="text-stone-800/70 dark:text-slate-300 hover:text-amber-700 dark:hover:text-blue-400 hover:bg-stone-100/50 dark:hover:bg-slate-800/50 font-medium px-3 py-2 rounded-lg transition">Mission</Link>
                <Link to="/library" className="text-stone-800/70 dark:text-slate-300 hover:text-amber-700 dark:hover:text-blue-400 hover:bg-stone-100/50 dark:hover:bg-slate-800/50 font-medium px-3 py-2 rounded-lg transition">Library</Link>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Dark Mode Toggle */}
              <motion.button 
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsDark(!isDark)}
                className="text-stone-800/50 dark:text-slate-400 hover:text-stone-800/70 dark:hover:text-slate-300 p-2 rounded-full hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition"
              >
                {isDark ? <Sun size={20} /> : <Moon size={20} />}
              </motion.button>

              {user ? (
                /* ── Logged In Nav ── */
                <>
                  <Link to="/settings" className="text-stone-800/50 dark:text-slate-400 hover:text-stone-800/70 dark:hover:text-slate-300 p-2 rounded-full hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition">
                    <SettingsIcon size={20} />
                  </Link>
                  <Link
                    to="/dashboard"
                    className="text-stone-800/70 dark:text-slate-300 hover:text-stone-900/80 dark:hover:text-white font-medium px-4 py-2 rounded-xl hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition hidden sm:flex items-center gap-2"
                  >
                    {profile?.avatar_url ? (
                      <img src={profile.avatar_url} alt="" className="w-6 h-6 rounded-full object-cover border border-white/50 dark:border-slate-600" />
                    ) : (
                      <UserCircle size={20} />
                    )}
                    <span className="max-w-[100px] truncate">
                      {profile?.full_name?.split(' ')[0] || 'Dashboard'}
                    </span>
                  </Link>
                  <motion.div whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }}>
                    <Link to="/scan" className="btn-premium-dark !px-5 !py-2 !rounded-xl !text-sm">
                      Scan
                    </Link>
                  </motion.div>
                </>
              ) : (
                /* ── Logged Out Nav ── */
                <>
                  <Link
                    to="/auth"
                    className="text-stone-800/70 dark:text-slate-300 hover:text-stone-900/80 dark:hover:text-white font-medium px-4 py-2 rounded-xl hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition hidden sm:block"
                  >
                    Sign In
                  </Link>
                  <motion.div whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }}>
                    <Link to="/scan" className="btn-premium-dark !px-5 !py-2 !rounded-xl !text-sm">
                      Scan
                    </Link>
                  </motion.div>
                </>
              )}
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 relative">
          <AnimatedRoutes />
        </main>
      </div>
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
