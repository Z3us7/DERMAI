import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Activity, Globe2, ArrowRight, Camera, Cpu, FileCheck2, Fingerprint } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LandingPage() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-5xl mx-auto px-4 py-16 space-y-24"
    >
      {/* Hero */}
      <div className="text-center space-y-6 pt-8">

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-stone-900/80 dark:text-white leading-[1.1]">
          Skin Disease Detection <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-stone-700 to-amber-600 dark:dark:from-stone-400 dark:to-amber-300">
            For Every Skin Tone
          </span>
        </h1>
        <p className="text-lg md:text-xl text-stone-800/70 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
          DermAI bridges the healthcare gap by providing instant, accurate dermatological screening 
          optimized for all Fitzpatrick skin types, especially darker skin tones.
        </p>
        <div className="pt-12 pb-8 flex flex-col items-center justify-center gap-8">
          <MagneticPillButton />
          <Link to="/about" className="text-stone-500 hover:text-stone-800 dark:text-slate-400 dark:hover:text-white transition font-medium tracking-wide">
            How we trained it
          </Link>
        </div>
        
        {/* Trust Banner */}
        <div className="pt-12 flex flex-wrap justify-center gap-8 text-stone-800/50 dark:text-slate-500 text-sm font-medium uppercase tracking-wider">
          <span className="flex items-center gap-2"><ShieldCheck size={18} /> HIPAA Compliant</span>
          <span className="flex items-center gap-2"><Globe2 size={18} /> 100k+ Diverse Images</span>
          <span className="flex items-center gap-2"><Activity size={18} /> 100+ Conditions</span>
        </div>
      </div>

      {/* How it Works */}
      <div className="space-y-12">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-stone-900/80 dark:text-white">How It Works</h2>
          <p className="text-stone-800/60 dark:text-slate-400 mt-2">Get clinical insights in under 30 seconds.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          <StepCard 
            number="1"
            icon={<Camera className="text-amber-600 dark:text-amber-400" size={32} />}
            title="Upload Image"
            description="Take a clear photo of your skin condition in good lighting. Our system ensures your image is securely processed."
          />
          <StepCard 
            number="2"
            icon={<Cpu className="text-orange-500 dark:text-indigo-400" size={32} />}
            title="AI Analysis"
            description="Our Vision Engine analyzes the image against over 100 known dermatological conditions with high precision."
          />
          <StepCard 
            number="3"
            icon={<FileCheck2 className="text-emerald-500 dark:text-emerald-400" size={32} />}
            title="Get Results"
            description="Receive immediate insights, confidence scores, and actionable next steps including when to consult a doctor."
          />
        </div>
      </div>

      {/* Features */}
      <div className="space-y-12 pb-16">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-stone-900/80 dark:text-white">Why Choose DermAI?</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard 
            icon={<Globe2 className="text-emerald-500 dark:text-emerald-400" size={32} />}
            title="Inclusive Training"
            description="Trained on the Fitzpatrick-17k dataset to eliminate the 35% error gap found in traditional AI models on darker skin."
          />
          <FeatureCard 
            icon={<Activity className="text-amber-600 dark:text-amber-400" size={32} />}
            title="Tropical Coverage"
            description="Recognizes over 100 conditions including neglected tropical diseases like Scabies and Tinea Versicolor."
          />
          <FeatureCard 
            icon={<ShieldCheck className="text-purple-500 dark:text-purple-400" size={32} />}
            title="Clinical Safety"
            description="Provides confidence scores, severity flags, and directs you to local dermatologists for proper care."
          />
        </div>
      </div>
    </motion.div>
  );
}

function StepCard({ title, description }) {
  return (
    <div className="glass-card relative space-y-3">
      <h3 className="text-xl font-semibold text-stone-900/80 dark:text-white">{title}</h3>
      <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}

function FeatureCard({ title, description }) {
  return (
    <div className="glass-card space-y-3 hover:border-stone-300/50 dark:hover:border-amber-600/30">
      <h3 className="text-xl font-semibold text-stone-900/80 dark:text-white">{title}</h3>
      <p className="text-stone-800/70 dark:text-slate-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}

function MagneticPillButton() {
  const buttonRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!buttonRef.current) return;
    const { left, top, width, height } = buttonRef.current.getBoundingClientRect();
    const x = e.clientX - left;
    const y = e.clientY - top;
    
    // Spotlight coordinates
    buttonRef.current.style.setProperty('--x', `${x}px`);
    buttonRef.current.style.setProperty('--y', `${y}px`);

    // Magnetic pull
    const moveX = (x - width / 2) * 0.15;
    const moveY = (y - height / 2) * 0.15;
    setPosition({ x: moveX, y: moveY });
  };

  const handleMouseLeave = () => {
    setHovered(false);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.div
      ref={buttonRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 150, damping: 15, mass: 0.1 }}
      whileTap={{ scale: 0.95 }}
      className="relative group cursor-pointer"
    >
      <Link
        to="/scan"
        className="relative flex items-center justify-center px-20 py-5 rounded-full bg-white/40 dark:bg-black/40 backdrop-blur-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.05)] transition-colors duration-500 hover:bg-white/50 dark:hover:bg-white/5"
      >
        {/* Spotlight Border/Background Glow */}
        <div 
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
          style={{
            background: `radial-gradient(120px circle at var(--x) var(--y), rgba(255,255,255,0.6) 0%, transparent 50%)`,
          }}
        />
        
        {/* Very thin glass border */}
        <div className="absolute inset-0 rounded-full border-[0.5px] border-stone-400/30 dark:border-white/20 pointer-events-none" />
        
        {/* Inner subtle rim highlight */}
        <div className="absolute inset-0 rounded-full shadow-[inset_0_1px_1px_rgba(255,255,255,0.9)] dark:shadow-[inset_0_1px_1px_rgba(255,255,255,0.2)] pointer-events-none" />

        <span className="relative z-10 text-stone-900 dark:text-white font-bold tracking-[0.35em] text-sm">
          SCAN
        </span>
      </Link>
    </motion.div>
  );
}
