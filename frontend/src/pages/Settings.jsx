import React, { useState, useEffect } from 'react';
import { User, Bell, Shield, Save, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, profile, updateProfile } = useAuth();
  
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [skinType, setSkinType] = useState('III');
  
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  // Initialize form with profile data
  useEffect(() => {
    if (profile) {
      const names = (profile.full_name || '').split(' ');
      setFirstName(names[0] || '');
      setLastName(names.slice(1).join(' ') || '');
      setSkinType(profile.skin_type || 'III');
    }
  }, [profile]);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSaved(false);

    try {
      const fullName = `${firstName.trim()} ${lastName.trim()}`.trim();
      
      const { error: updateErr } = await updateProfile({
        full_name: fullName,
        skin_type: skinType,
      });

      if (updateErr) throw updateErr;

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Update profile error:', err);
      setError(err.message || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-4xl mx-auto px-4 py-12 space-y-8"
    >
      <div>
        <h1 className="text-3xl font-bold text-stone-900/80 dark:text-white mb-2">Profile Settings</h1>
        <p className="text-stone-800/60 dark:text-slate-400">Manage your account preferences and clinical data.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-stone-100 dark:bg-slate-800 text-amber-800 dark:text-amber-400 font-medium">
            <User size={20} /> Personal Info
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-stone-800/70 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800 hover:text-stone-900/80 dark:hover:text-white transition opacity-50 cursor-not-allowed">
            <Bell size={20} /> Notifications
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-stone-800/70 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800 hover:text-stone-900/80 dark:hover:text-white transition opacity-50 cursor-not-allowed">
            <Shield size={20} /> Privacy
          </button>
        </div>

        <div className="md:col-span-2">
          <div className="glass-card">
            <h2 className="text-xl font-semibold text-stone-900/80 dark:text-white mb-6">Personal Information</h2>
            
            <form onSubmit={handleSave} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-stone-700/80 dark:text-slate-300">First Name</label>
                  <input 
                    type="text" 
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:border-amber-600 focus:ring-2 focus:ring-blue-200 outline-none bg-white/50 dark:bg-slate-900/50 dark:text-white" 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-stone-700/80 dark:text-slate-300">Last Name</label>
                  <input 
                    type="text" 
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:border-amber-600 focus:ring-2 focus:ring-blue-200 outline-none bg-white/50 dark:bg-slate-900/50 dark:text-white" 
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-stone-700/80 dark:text-slate-300">Email Address</label>
                <input 
                  type="email" 
                  value={user?.email || ''} 
                  disabled
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 bg-stone-100/50 dark:bg-slate-800/50 dark:text-slate-400 cursor-not-allowed" 
                />
                <p className="text-xs text-stone-500">Email cannot be changed directly.</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-stone-700/80 dark:text-slate-300">Fitzpatrick Skin Type</label>
                <select 
                  value={skinType}
                  onChange={(e) => setSkinType(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 focus:border-amber-600 focus:ring-2 focus:ring-blue-200 outline-none bg-white/50 dark:bg-slate-900/50 dark:text-white appearance-none"
                >
                  <option value="I">Type I (Light, Pale White)</option>
                  <option value="II">Type II (White, Fair)</option>
                  <option value="III">Type III (Medium White to Olive)</option>
                  <option value="IV">Type IV (Olive, Moderate Brown)</option>
                  <option value="V">Type V (Brown, Dark Brown)</option>
                  <option value="VI">Type VI (Very Dark Brown to Black)</option>
                </select>
                <p className="text-xs text-stone-800/60 dark:text-slate-400">Helps our AI calibrate its confidence scores more accurately.</p>
              </div>

              {error && (
                <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded-xl flex gap-2.5 text-sm border border-red-100 dark:border-red-800/50">
                  <AlertCircle className="shrink-0 mt-0.5" size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className="pt-4 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
                <span className="text-sm text-emerald-600 dark:text-emerald-400 font-medium h-5">
                  {saved ? 'Changes saved successfully!' : ''}
                </span>
                <motion.button 
                  type="submit" 
                  disabled={loading}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 400, damping: 17 }}
                  className="bg-stone-800 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-stone-900 transition flex items-center gap-2 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : <><Save size={18} /> Save Changes</>}
                </motion.button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
