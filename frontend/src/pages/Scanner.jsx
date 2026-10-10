import React, { useState, useRef } from 'react';
import { Camera, AlertCircle, RefreshCw, ChevronLeft, Info, Volume2, BookOpen, Check, Save } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Scanner() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Save-to-history state
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const fileInputRef = useRef(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResults(null);
    setError(null);
    setSaved(false);
    setSaveError(null);
  };

  const analyzeImage = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
      const res = await fetch(`${API_URL}/api/v1/analyze`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail?.detail || data.detail || 'Analysis failed');
      }
      
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /** Upload image to Supabase Storage and save scan result to database */
  const saveScan = async () => {
    if (!results || !file || !user || saved) return;
    setSaving(true);
    setSaveError(null);

    try {
      // 1. Upload image to Supabase Storage
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}/${Date.now()}.${fileExt}`;

      const { error: uploadError } = await supabase.storage
        .from('scan-images')
        .upload(fileName, file, {
          cacheControl: '3600',
          upsert: false,
        });

      if (uploadError) throw uploadError;

      // 2. Get the public URL for the uploaded image
      const { data: urlData } = supabase.storage
        .from('scan-images')
        .getPublicUrl(fileName);

      // 3. Insert scan result into the database
      const { error: insertError } = await supabase
        .from('scan_results')
        .insert({
          user_id: user.id,
          image_url: urlData.publicUrl,
          top_prediction: results.predictions[0].disease_name,
          confidence: results.predictions[0].confidence,
          all_predictions: results.predictions,
          patient_explanation: results.patient_explanation || null,
        });

      if (insertError) throw insertError;

      setSaved(true);
    } catch (err) {
      console.error('Save scan error:', err);
      setSaveError(err.message || 'Failed to save scan. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const resetScanner = () => {
    setResults(null);
    setFile(null);
    setPreview(null);
    setSaved(false);
    setSaveError(null);
    setError(null);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className="max-w-2xl mx-auto px-4 py-8"
    >
      <Link to="/" className="inline-flex items-center text-stone-800/60 dark:text-slate-400 hover:text-stone-800/80 dark:hover:text-slate-200 transition mb-6 bg-white/50 dark:bg-slate-800/50 px-3 py-1.5 rounded-full backdrop-blur-sm border border-slate-200 dark:border-slate-700 shadow-sm">
        <ChevronLeft size={18} className="mr-1" /> Back
      </Link>

      {!results ? (
        <div className="space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-stone-900/80 dark:text-white">Clinical Skin Scanner</h1>
            <p className="text-stone-800/60 dark:text-slate-400 mt-2 text-sm">Please ensure good lighting and clear focus.</p>
          </div>

          <motion.div 
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="glass-card !p-2 relative overflow-hidden group border-dashed border-2 border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-amber-600 hover:bg-stone-100/30 dark:hover:bg-stone-900/20 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="h-64 md:h-80 w-full rounded-2xl flex flex-col items-center justify-center overflow-hidden relative">
              {preview ? (
                <>
                  <img src={preview} alt="Preview" className="w-full h-full object-contain bg-black/5 dark:bg-black/20 rounded-2xl" />
                  {loading && (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 bg-white/40 dark:bg-black/40 backdrop-blur-md flex flex-col items-center justify-center z-10 rounded-2xl"
                    >
                      <motion.div
                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        className="w-20 h-20 rounded-full border-4 border-amber-600/30 border-t-amber-600 animate-spin mb-4 shadow-lg"
                      />
                      <p className="text-amber-800 dark:text-amber-400 font-semibold tracking-wider uppercase text-sm drop-shadow-md">Running AI Analysis...</p>
                    </motion.div>
                  )}
                </>
              ) : (
                <div className="text-stone-800/50 flex flex-col items-center">
                  <div className="w-16 h-16 bg-stone-200 dark:bg-stone-900/50 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <Camera size={32} />
                  </div>
                  <span className="font-medium text-stone-800/70 dark:text-slate-400">Tap to Capture or Upload</span>
                </div>
              )}
            </div>
            <input 
              type="file" 
              ref={fileInputRef}
              className="hidden" 
              accept="image/jpeg,image/png"
              onChange={handleFileChange} 
            />
          </motion.div>

          <div className="bg-stone-100/80 dark:bg-stone-900/30 backdrop-blur-sm text-blue-800 dark:text-blue-300 p-4 rounded-xl flex gap-3 text-sm border border-stone-200 dark:border-stone-800/50">
            <Info className="shrink-0 text-amber-700 dark:text-amber-400" size={20} />
            <p>Your image is processed securely and is never used for advertising.</p>
          </div>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-4 rounded-xl flex gap-3 text-sm border border-red-100 dark:border-red-800/50">
              <AlertCircle className="shrink-0" size={20} />
              {error}
            </div>
          )}

          <motion.button
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            onClick={analyzeImage}
            disabled={!file || loading}
            className="btn-premium-dark w-full !rounded-xl"
          >
            {loading ? <><RefreshCw className="animate-spin" size={20} /> Analyzing...</> : 'Analyze Image'}
          </motion.button>
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {results.predictions[0].confidence < 0.60 ? (
            <div className="glass-card bg-amber-50/80 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/50 space-y-4">
              <div className="flex items-center gap-3 text-amber-800 dark:text-amber-500">
                <AlertCircle size={28} className="shrink-0" />
                <h2 className="text-xl font-bold">Inconclusive Result</h2>
              </div>
              <p className="text-amber-900 dark:text-amber-200/80 text-sm leading-relaxed">
                The condition in the image does not strongly match any disease in our current AI vocabulary (confidence is below 60%). Please consult a dermatologist for a professional medical evaluation.
              </p>
            </div>
          ) : (
            <>
              <div className="glass-card flex gap-5 items-center">
                <img src={preview} className="w-24 h-24 rounded-xl object-cover shadow-sm border border-white/50 dark:border-slate-700" alt="Scanned" />
                <div>
                  <h2 className="text-2xl font-bold text-stone-900/80 dark:text-white">{results.predictions[0].disease_name}</h2>
                  <span className="inline-block mt-1 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-stone-800/70 dark:text-slate-300 rounded-md text-sm font-medium font-mono border border-slate-200 dark:border-slate-700">
                    Confidence: {(results.predictions[0].confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="glass-card space-y-5">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-stone-800/80 dark:text-slate-200 uppercase tracking-wider text-xs">Diagnostic Matches</h3>
                </div>
                <div className="space-y-4">
                  {results.predictions.map((pred, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-stone-700/80 dark:text-slate-300 font-medium">{pred.disease_name}</span>
                        <span className="text-stone-800/60 dark:text-slate-400">{(pred.confidence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-2.5 w-full bg-slate-100/80 dark:bg-slate-800/80 rounded-full overflow-hidden shadow-inner">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${pred.confidence * 100}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                          className={`h-full rounded-full ${i === 0 ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'bg-slate-300 dark:bg-slate-600'}`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card bg-emerald-50/80 dark:bg-emerald-900/20 border-emerald-100/50 dark:border-emerald-800/50 space-y-3 relative shadow-sm">
                 <button className="absolute top-4 right-4 text-emerald-600 dark:text-emerald-400 bg-white dark:bg-slate-800 p-2 rounded-full shadow-sm hover:scale-105 transition border border-transparent dark:border-slate-700">
                   <Volume2 size={18} />
                 </button>
                <h3 className="font-semibold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider text-xs flex items-center gap-1">
                  <Info size={14} /> Clinical Note
                </h3>
                <p className="text-emerald-900 dark:text-emerald-100/80 text-sm leading-relaxed pr-8">
                  {results.patient_explanation}
                </p>
              </div>

              {/* Next Steps Card */}
              <div className="glass-card space-y-3">
                <h3 className="font-semibold text-stone-800/80 dark:text-slate-200 uppercase tracking-wider text-xs flex items-center gap-1">
                  <BookOpen size={14} /> Next Steps
                </h3>
                <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">
                  Based on this prediction, you can read more about standard care guidelines in our Skin Health Library. 
                </p>
                <Link to="/library" className="inline-flex items-center text-amber-700 dark:text-amber-400 text-sm font-medium hover:underline">
                  Learn about {results.predictions[0].disease_name} &rarr;
                </Link>
              </div>
            </>
          )}

          {/* Save Error */}
          {saveError && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded-xl flex gap-2.5 text-sm border border-red-100 dark:border-red-800/50"
            >
              <AlertCircle className="shrink-0 mt-0.5" size={16} />
              <span>{saveError}</span>
            </motion.div>
          )}

          <div className="pt-2 flex gap-4">
             <motion.div whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }} className="flex-1">
               <button
                 onClick={saved ? () => navigate('/dashboard') : saveScan}
                 disabled={saving}
                 className={`w-full inline-flex items-center justify-center gap-2 ${
                   saved
                     ? 'btn-premium !bg-emerald-50 dark:!bg-emerald-900/30 !text-emerald-700 dark:!text-emerald-400 !border-emerald-200 dark:!border-emerald-800'
                     : 'btn-premium'
                 } !px-2`}
               >
                 {saving ? (
                   <><RefreshCw className="animate-spin" size={16} /> Saving...</>
                 ) : saved ? (
                   <><Check size={16} /> View Dashboard</>
                 ) : (
                   <><Save size={16} /> Save to History</>
                 )}
               </button>
             </motion.div>
             <motion.button 
                onClick={resetScanner} 
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                className="btn-premium-dark w-full flex-1 !px-2"
              >
              Scan Another
             </motion.button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
