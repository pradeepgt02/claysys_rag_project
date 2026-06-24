import React from 'react';
import { ArrowRight, Sparkles, MessageSquare, Database, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const LandingHero: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-32 lg:pt-32 flex flex-col lg:flex-row items-center gap-16 relative">
      {/* Background gradients */}
      <div className="absolute top-1/2 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-violet-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 right-1/4 translate-x-1/4 -translate-y-1/2 w-[400px] h-[400px] bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none" />

      {/* Text Content */}
      <div className="flex-1 text-center lg:text-left z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-slate-300 mb-8">
          <Sparkles className="w-4 h-4 text-violet-400" />
          Retrieval-Augmented Generation
        </div>
        
        <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
          Chat with <br className="hidden lg:block" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400">
            any website.
          </span>
        </h1>
        
        <p className="text-lg text-slate-400 mb-10 max-w-xl mx-auto lg:mx-0 leading-relaxed">
          WebMind ingests a URL, recursively crawls relevant pages, and answers questions with accurate cited AI responses.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
          <button 
            onClick={() => navigate('/workspace')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white text-slate-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-slate-200 transition-colors shadow-[0_0_40px_rgba(255,255,255,0.1)]"
          >
            Get started free
            <ArrowRight className="w-5 h-5" />
          </button>
          <button 
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-bold text-lg bg-white/5 text-white hover:bg-white/10 transition-colors border border-white/10"
          >
            See how it works
          </button>
        </div>
      </div>

      {/* Right Side Illustration */}
      <div className="flex-1 w-full max-w-lg lg:max-w-none relative z-10 hidden md:block">
        <div className="relative aspect-square w-full">
          {/* Main card */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-96 bg-slate-900/80 backdrop-blur-2xl border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col z-20">
            <div className="h-12 border-b border-white/10 flex items-center px-4 gap-2 bg-white/5">
              <div className="w-3 h-3 rounded-full bg-rose-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            </div>
            <div className="p-6 flex-1 flex flex-col gap-4">
              <div className="w-3/4 h-6 bg-white/5 rounded-lg" />
              <div className="w-full h-4 bg-white/5 rounded-lg" />
              <div className="w-5/6 h-4 bg-white/5 rounded-lg" />
              
              <div className="mt-auto bg-violet-500/10 border border-violet-500/20 p-4 rounded-xl flex items-start gap-3">
                <div className="p-2 bg-violet-500/20 rounded-lg text-violet-400 shrink-0">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div className="flex flex-col gap-2 w-full mt-1">
                  <div className="w-full h-3 bg-violet-400/20 rounded" />
                  <div className="w-2/3 h-3 bg-violet-400/20 rounded" />
                </div>
              </div>
            </div>
          </div>
          
          {/* Floating elements */}
          <div className="absolute top-1/4 right-0 w-32 h-32 bg-indigo-500/20 backdrop-blur-xl border border-indigo-500/30 rounded-2xl shadow-xl flex items-center justify-center animate-[bounce_4s_infinite] z-30">
            <Globe className="w-12 h-12 text-indigo-400" />
          </div>
          
          <div className="absolute bottom-1/4 left-0 w-24 h-24 bg-purple-500/20 backdrop-blur-xl border border-purple-500/30 rounded-2xl shadow-xl flex items-center justify-center animate-[bounce_5s_infinite_0.5s] z-30">
            <Database className="w-10 h-10 text-purple-400" />
          </div>
        </div>
      </div>
    </div>
  );
};
