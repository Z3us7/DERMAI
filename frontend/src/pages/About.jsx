import React from 'react';
import { ShieldCheck, HeartPulse, BrainCircuit, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function About() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-4xl mx-auto px-4 py-16 space-y-16"
    >
      <div className="text-center space-y-6">
        <h1 className="text-4xl md:text-5xl font-bold text-stone-900/80 dark:text-white">Our Mission</h1>
        <p className="text-lg text-stone-800/70 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
          We believe that accurate, clinical-grade dermatological AI should be accessible to everyone, regardless of their skin tone or geographic location.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 pt-8">
        <div className="glass-card space-y-4 hover:-translate-y-1 transition-transform">
          <h3 className="text-xl font-semibold text-stone-900/80 dark:text-white">Inclusive Healthcare</h3>
          <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">
            Traditional AI models have a 35% error gap on darker skin tones. DermAI was trained specifically on the Diverse Dermatology Images (DDI) dataset to ensure equity.
          </p>
        </div>
        
        <div className="glass-card space-y-4 hover:-translate-y-1 transition-transform">
          <h3 className="text-xl font-semibold text-stone-900/80 dark:text-white">Advanced AI</h3>
          <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">
            Our models can detect over 100 conditions, including neglected tropical diseases, providing confidence scores and actionable next steps.
          </p>
        </div>

        <div className="glass-card space-y-4 hover:-translate-y-1 transition-transform">
          <h3 className="text-xl font-semibold text-stone-900/80 dark:text-white">Privacy First</h3>
          <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">
            Your images are processed securely, are never stored without explicit permission, and are never used for advertising purposes. HIPAA compliant design.
          </p>
        </div>
      </div>
      
      <div className="glass-card bg-stone-100/50 dark:bg-stone-900/10 border-stone-200 dark:border-stone-800/30 mt-16 text-center py-12">
        <h2 className="text-2xl font-bold text-stone-900/80 dark:text-white mb-4">Ready to try it out?</h2>
        <motion.div whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 17 }} className="inline-block">
          <Link to="/scan" className="btn-premium-dark">
            Start a Free Scan
          </Link>
        </motion.div>
      </div>
    </motion.div>
  );
}
