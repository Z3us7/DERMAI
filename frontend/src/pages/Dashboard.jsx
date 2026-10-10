import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { History, Calendar, MapPin, User, ChevronRight, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';

export default function Dashboard() {
  const { user, profile } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) return;
    
    const fetchHistory = async () => {
      try {
        const { data, error } = await supabase
          .from('scan_results')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (error) throw error;
        setHistory(data || []);
      } catch (err) {
        console.error('Error fetching history:', err);
        setError('Failed to load scan history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [user]);

  // Compute severity from confidence for display purposes
  const getSeverityLabel = (confidence) => {
    if (confidence > 0.9) return 'High Confidence';
    if (confidence > 0.7) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-5xl mx-auto px-4 py-12 space-y-8"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-stone-900/80 dark:text-white">Patient Dashboard</h1>
          <p className="text-stone-800/60 dark:text-slate-400 mt-1">Manage your condition tracking and records</p>
        </div>
        <motion.div whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }}>
          <Link to="/scan" className="bg-stone-800 text-white px-6 py-2.5 rounded-full font-medium hover:bg-stone-900 transition shadow-sm hover:shadow block">
            New Scan
          </Link>
        </motion.div>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {/* Profile Sidebar */}
        <div className="md:col-span-1 space-y-6">
          <div className="glass-card space-y-4">
            <div className="w-20 h-20 bg-gradient-to-tr from-amber-100 to-orange-50 dark:from-blue-900/50 dark:to-indigo-900/50 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center mx-auto mb-2 shadow-inner border border-white dark:border-amber-600/30 overflow-hidden">
              {profile?.avatar_url ? (
                <img src={profile.avatar_url} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User size={36} />
              )}
            </div>
            <div className="text-center">
              <h2 className="font-semibold text-xl text-stone-900/80 dark:text-white">
                {profile?.full_name || 'Patient'}
              </h2>
              <p className="text-sm text-stone-800/60 dark:text-slate-400 font-medium">
                Fitzpatrick Type {profile?.skin_type || 'III'}
              </p>
            </div>
            <div className="border-t border-slate-200/60 dark:border-slate-700/60 pt-4 space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-stone-800/60 dark:text-slate-400">Language</span>
                <span className="font-medium text-stone-700/80 dark:text-slate-300 bg-white/50 dark:bg-slate-800/50 px-2 py-0.5 rounded-md">
                  {profile?.language === 'en' ? 'English' : profile?.language || 'English'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-800/60 dark:text-slate-400">Location</span>
                <span className="font-medium text-stone-700/80 dark:text-slate-300 bg-white/50 dark:bg-slate-800/50 px-2 py-0.5 rounded-md">
                  {profile?.location || 'India'}
                </span>
              </div>
            </div>
            <Link to="/settings" className="block text-center text-sm text-amber-700 dark:text-amber-400 font-medium hover:underline pt-2">
              Edit Profile
            </Link>
          </div>

          <div className="glass-card bg-stone-100/50 dark:bg-stone-900/10 border-stone-200/50 dark:border-stone-800/30 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-amber-400/10 dark:bg-stone-1000/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
            <h3 className="font-semibold text-amber-900 dark:text-blue-300 mb-2 flex items-center gap-2 relative z-10">
              <MapPin size={18} /> Find a Doctor
            </h3>
            <p className="text-sm text-amber-800 dark:text-amber-400/80 mb-4 relative z-10">
              Connect with nearby dermatologists accepting your insurance.
            </p>
            <motion.button whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }} className="w-full bg-white dark:bg-slate-800 border border-stone-300 dark:border-stone-800/50 text-amber-700 dark:text-amber-400 py-2.5 rounded-xl font-medium hover:bg-stone-100 dark:hover:bg-slate-700 transition relative z-10 shadow-sm">
              Search Directory
            </motion.button>
          </div>
        </div>

        {/* Timeline Feed & Progress */}
        <div className="md:col-span-2 space-y-6">
          {history.length > 0 && (
            <div className="glass-card flex items-center justify-between bg-gradient-to-r from-emerald-50/50 to-transparent dark:from-emerald-900/20 dark:to-transparent">
              <div>
                <h3 className="text-lg font-bold text-stone-900/80 dark:text-white flex items-center gap-2">
                  <TrendingDown className="text-emerald-500 dark:text-emerald-400" /> Tracking Active
                </h3>
                <p className="text-sm text-stone-800/60 dark:text-slate-400 mt-1">You have {history.length} scans recorded.</p>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mb-2 pt-2">
            <div className="flex items-center gap-2">
              <History className="text-stone-800/50 dark:text-slate-500" size={20} />
              <h2 className="text-xl font-bold text-stone-800/80 dark:text-white">Longitudinal Tracking</h2>
            </div>
          </div>

          {loading ? (
            <div className="glass-card flex flex-col items-center justify-center py-12 text-stone-500 dark:text-slate-400">
              <RefreshCw className="animate-spin mb-3" size={28} />
              <p>Loading your history...</p>
            </div>
          ) : error ? (
            <div className="glass-card flex flex-col items-center justify-center py-8 text-red-600 dark:text-red-400 bg-red-50/50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/30">
              <AlertCircle size={28} className="mb-2" />
              <p>{error}</p>
            </div>
          ) : history.length === 0 ? (
            <div className="glass-card flex flex-col items-center justify-center py-16 text-stone-500 dark:text-slate-400 border-dashed border-2">
              <div className="bg-stone-100 dark:bg-slate-800 p-4 rounded-full mb-4">
                <History size={32} />
              </div>
              <p className="font-medium text-lg text-stone-700 dark:text-slate-300">No scans yet</p>
              <p className="text-sm mt-1">Your scan history will appear here.</p>
              <Link to="/scan" className="mt-6 text-amber-700 dark:text-amber-400 font-medium hover:underline">
                Take your first scan &rarr;
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((record, index) => (
                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  key={record.id} 
                  className="glass-card p-4 flex flex-col sm:flex-row gap-4 hover:border-blue-300 dark:hover:border-amber-600/50 hover:shadow-md transition-all cursor-pointer group"
                >
                  <div className="w-full sm:w-28 h-40 sm:h-28 rounded-xl overflow-hidden bg-stone-100 dark:bg-slate-800 shrink-0 border border-white/80 dark:border-white/10 shadow-sm relative">
                    <img 
                      src={record.image_url} 
                      alt={record.top_prediction} 
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 flex flex-col justify-between">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-lg text-stone-900/80 dark:text-white group-hover:text-amber-700 dark:group-hover:text-blue-400 transition-colors">
                          {record.top_prediction}
                        </h3>
                        <div className="flex items-center gap-1.5 text-sm text-stone-800/60 dark:text-slate-400 mt-1">
                          <Calendar size={14} /> 
                          {new Date(record.created_at).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </div>
                      </div>
                      <div className="bg-slate-100/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 text-stone-700/80 dark:text-slate-300 px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wide text-center">
                        <div>Conf</div>
                        <div className="text-amber-700 dark:text-amber-400">
                          {(record.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3">
                      <span className={`text-sm font-semibold flex items-center gap-1.5 ${record.confidence > 0.8 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400'}`}>
                        <span className={`w-2 h-2 rounded-full ${record.confidence > 0.8 ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
                        {getSeverityLabel(record.confidence)}
                      </span>
                      <ChevronRight size={18} className="text-slate-300 dark:text-slate-600 group-hover:text-amber-600 dark:group-hover:text-blue-400 transition-colors" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
