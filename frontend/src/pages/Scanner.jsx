import React, { useState, useRef } from 'react';
import { Camera, AlertCircle, RefreshCw, ChevronLeft, Info, Volume2, BookOpen, Check, Save, Image as ImageIcon, Crop } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';
import ReactCrop, { centerCrop, makeAspectCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function centerAspectCrop(mediaWidth, mediaHeight, aspect) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: '%',
        width: 80,
      },
      aspect,
      mediaWidth,
      mediaHeight
    ),
    mediaWidth,
    mediaHeight
  );
}

export default function Scanner() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Cropper states
  const [imgSrc, setImgSrc] = useState('');
  const imgRef = useRef(null);
  const [crop, setCrop] = useState();
  const [completedCrop, setCompletedCrop] = useState(null);
  const [showCropper, setShowCropper] = useState(false);

  // Save-to-history state
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    
    // Reset states
    setFile(null);
    setPreview(null);
    setResults(null);
    setError(null);
    setSaved(false);
    setSaveError(null);
    setCrop(undefined);

    const reader = new FileReader();
    reader.addEventListener('load', () => {
      setImgSrc(reader.result?.toString() || '');
      setShowCropper(true);
    });
    reader.readAsDataURL(selectedFile);
  };

  const onImageLoad = (e) => {
    const { width, height } = e.currentTarget;
    setCrop(centerAspectCrop(width, height, 1));
  };

  const confirmCrop = async () => {
    if (!completedCrop || !imgRef.current) return;
    
    const image = imgRef.current;
    const canvas = document.createElement('canvas');
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;
    
    const targetWidth = completedCrop.width * scaleX;
    const targetHeight = completedCrop.height * scaleY;

    if (targetWidth <= 0 || targetHeight <= 0) {
       setShowCropper(false);
       return;
    }

    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    ctx.drawImage(
      image,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      targetWidth,
      targetHeight,
      0,
      0,
      targetWidth,
      targetHeight
    );

    canvas.toBlob((blob) => {
      if (!blob) return;
      const croppedFile = new File([blob], 'cropped-scan.jpg', { type: 'image/jpeg' });
      setFile(croppedFile);
      setPreview(URL.createObjectURL(blob));
      setShowCropper(false);
    }, 'image/jpeg');
  };

  const cancelCrop = () => {
    setShowCropper(false);
    setImgSrc('');
    setFile(null);
    setPreview(null);
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

  const saveScan = async () => {
    if (!results || !file || !user || saved) return;
    setSaving(true);
    setSaveError(null);

    try {
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}/${Date.now()}.${fileExt}`;

      const { error: uploadError } = await supabase.storage
        .from('scan-images')
        .upload(fileName, file, { cacheControl: '3600', upsert: false });

      if (uploadError) throw uploadError;

      const { data: urlData } = supabase.storage
        .from('scan-images')
        .getPublicUrl(fileName);

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

      {/* Cropper Modal */}
      <AnimatePresence>
        {showCropper && !!imgSrc && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          >
            <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-stone-50 dark:bg-slate-800/50">
                <h3 className="font-bold text-stone-900 dark:text-white flex items-center gap-2">
                  <Crop size={18} className="text-amber-600 dark:text-amber-400" /> 
                  Crop Image
                </h3>
                <p className="text-xs text-stone-500 dark:text-slate-400 font-medium">Focus on the affected skin area</p>
              </div>
              <div className="flex-1 overflow-y-auto p-4 flex justify-center bg-stone-900/5 dark:bg-black/50 min-h-[300px] items-center">
                <ReactCrop
                  crop={crop}
                  onChange={(_, percentCrop) => setCrop(percentCrop)}
                  onComplete={(c) => setCompletedCrop(c)}
                  aspect={1}
                  circularCrop={false}
                >
                  <img
                    ref={imgRef}
                    alt="Crop me"
                    src={imgSrc}
                    onLoad={onImageLoad}
                    className="max-h-[60vh] object-contain"
                  />
                </ReactCrop>
              </div>
              <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3 bg-stone-50 dark:bg-slate-800/50">
                <button 
                  onClick={cancelCrop}
                  className="px-5 py-2.5 rounded-xl font-medium text-stone-700 dark:text-slate-300 hover:bg-stone-200 dark:hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={confirmCrop}
                  className="btn-premium !py-2.5 !px-6 flex items-center gap-2"
                >
                  <Check size={18} /> Confirm Crop
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!results ? (
        <div className="space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-stone-900/80 dark:text-white">Clinical Skin Scanner</h1>
            <p className="text-stone-800/60 dark:text-slate-400 mt-2 text-sm">Ensure good lighting and crop close to the condition.</p>
          </div>

          <div className="glass-card !p-4 relative">
            {preview ? (
              <div className="h-64 md:h-80 w-full rounded-2xl flex flex-col items-center justify-center overflow-hidden relative border border-slate-200 dark:border-slate-700">
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
                
                {!loading && (
                  <button 
                    onClick={() => {
                      setPreview(null);
                      setFile(null);
                    }}
                    className="absolute top-3 right-3 bg-white/80 dark:bg-black/50 backdrop-blur text-stone-800 dark:text-white p-2 rounded-full hover:bg-white dark:hover:bg-slate-800 shadow-sm transition"
                  >
                    <RefreshCw size={16} />
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => cameraInputRef.current?.click()}
                  className="h-48 md:h-64 rounded-2xl flex flex-col items-center justify-center border-dashed border-2 border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-amber-600 bg-stone-50/50 dark:bg-stone-900/20 hover:bg-stone-100/50 dark:hover:bg-stone-900/40 transition-colors group cursor-pointer"
                >
                  <div className="w-14 h-14 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <Camera size={28} />
                  </div>
                  <span className="font-semibold text-stone-800/80 dark:text-slate-300 text-center px-2">Take a Photo</span>
                </motion.button>

                <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => fileInputRef.current?.click()}
                  className="h-48 md:h-64 rounded-2xl flex flex-col items-center justify-center border-dashed border-2 border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-amber-600 bg-stone-50/50 dark:bg-stone-900/20 hover:bg-stone-100/50 dark:hover:bg-stone-900/40 transition-colors group cursor-pointer"
                >
                  <div className="w-14 h-14 bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <ImageIcon size={28} />
                  </div>
                  <span className="font-semibold text-stone-800/80 dark:text-slate-300 text-center px-2">Upload Image</span>
                </motion.button>
              </div>
            )}

            {/* Hidden Inputs */}
            <input 
              type="file" 
              ref={cameraInputRef}
              className="hidden" 
              accept="image/*"
              capture="environment"
              onChange={handleFileChange} 
            />
            <input 
              type="file" 
              ref={fileInputRef}
              className="hidden" 
              accept="image/jpeg,image/png"
              onChange={handleFileChange} 
            />
          </div>

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
          <>
            <div className="glass-card flex gap-5 items-center">
              <img src={preview} className="w-24 h-24 rounded-xl object-cover shadow-sm border border-white/50 dark:border-slate-700" alt="Scanned" />
              <div>
                <h2 className="text-2xl font-bold text-stone-900/80 dark:text-white">{results.predictions[0].disease_name}</h2>
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
