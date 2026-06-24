import React from 'react';
import { BrainCircuit } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const LandingNavbar: React.FC = () => {
  const navigate = useNavigate();

  return (
    <nav className="w-full flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#030712]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-violet-500/20 rounded-lg text-violet-400">
          <BrainCircuit className="w-5 h-5" />
        </div>
        <span className="text-lg font-bold tracking-tight text-slate-100">WebMind</span>
      </div>
      
      <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
        <a href="#how-it-works" className="hover:text-slate-100 transition-colors">How it works</a>
        <a href="#features" className="hover:text-slate-100 transition-colors">Features</a>
      </div>

      <div>
        <button 
          onClick={() => navigate('/workspace')}
          className="px-4 py-2 bg-slate-100 text-slate-900 text-sm font-semibold rounded-lg hover:bg-white transition-colors"
        >
          Open App
        </button>
      </div>
    </nav>
  );
};
