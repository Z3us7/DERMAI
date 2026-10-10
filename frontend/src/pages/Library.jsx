import React, { useState } from 'react';
import { Search, BookOpen, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const CONDITIONS = [
  {
    name: 'Eczema (Atopic Dermatitis)',
    category: 'Inflammatory',
    description: 'A condition that makes your skin red and itchy. It is common in children but can occur at any age.',
    advice: 'Keep skin moisturized, avoid harsh soaps, and use prescribed topical treatments during flare-ups.'
  },
  {
    name: 'Melanoma',
    category: 'Malignant',
    description: 'The most serious type of skin cancer, develops in the cells (melanocytes) that produce melanin.',
    advice: 'URGENT: Requires immediate evaluation by a dermatologist. Look for asymmetric moles with irregular borders.'
  },
  {
    name: 'Scabies',
    category: 'Infectious',
    description: 'An itchy skin condition caused by a tiny burrowing mite called Sarcoptes scabiei.',
    advice: 'Requires prescription scabicides. All household members and close contacts should be treated simultaneously.'
  },
  {
    name: 'Psoriasis',
    category: 'Autoimmune',
    description: 'A skin disease that causes red, itchy scaly patches, most commonly on the knees, elbows, trunk and scalp.',
    advice: 'Manage triggers (stress, cold weather), use moisturizers, and consult a doctor for systemic or topical therapies.'
  },
  {
    name: 'Tinea Versicolor',
    category: 'Fungal',
    description: 'A common fungal infection of the skin. The fungus interferes with the normal pigmentation of the skin.',
    advice: 'Treated with over-the-counter or prescription antifungal creams, lotions, or shampoos.'
  }
];

export default function Library() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredConditions = CONDITIONS.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-4xl mx-auto px-4 py-12 space-y-8"
    >
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-stone-900/80 dark:text-white mb-2 flex items-center gap-2">
            <BookOpen size={28} className="text-amber-700 dark:text-amber-400" /> Skin Health Library
          </h1>
          <p className="text-stone-800/60 dark:text-slate-400">Learn about conditions our AI can detect and basic care guidelines.</p>
        </div>
        
        <div className="relative max-w-sm w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-800/50 dark:text-slate-500" size={20} />
          <input 
            type="text" 
            placeholder="Search conditions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 dark:border-white/10 focus:border-amber-600 focus:ring-2 focus:ring-blue-200 outline-none transition bg-white/50 dark:bg-white/5 backdrop-blur-sm text-stone-900/80 dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
          />
        </div>
      </div>

      <div className="grid gap-6">
        {filteredConditions.map((condition, idx) => (
          <div key={idx} className="glass-card flex flex-col md:flex-row md:items-center gap-6 group hover:border-stone-300 dark:hover:border-amber-600/30">
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-bold text-stone-900/80 dark:text-white">{condition.name}</h3>
                <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 dark:bg-white/10 text-stone-800/70 dark:text-slate-300">
                  {condition.category}
                </span>
              </div>
              <p className="text-stone-800/70 dark:text-slate-400 text-sm">{condition.description}</p>
              
              <div className="pt-2">
                <h4 className="text-sm font-semibold text-stone-800/80 dark:text-slate-200 mb-1">General Advice</h4>
                <p className="text-sm text-stone-800/70 dark:text-slate-400 border-l-2 border-amber-600 dark:border-blue-400 pl-3 py-0.5">
                  {condition.advice}
                </p>
              </div>
            </div>
            <button className="md:w-auto w-full flex items-center justify-center gap-2 text-amber-700 dark:text-amber-400 font-medium px-4 py-2 rounded-lg hover:bg-stone-100 dark:hover:bg-stone-900/20 transition">
              Read More <ChevronRight size={18} />
            </button>
          </div>
        ))}
        {filteredConditions.length === 0 && (
          <div className="text-center py-12 text-stone-800/60 dark:text-slate-400">
            No conditions found matching "{searchTerm}"
          </div>
        )}
      </div>
    </motion.div>
  );
}
