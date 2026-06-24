import React from 'react';
import { LandingNavbar } from '../components/LandingNavbar';
import { LandingHero } from '../components/LandingHero';
import { HowItWorks } from '../components/HowItWorks';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 font-sans selection:bg-violet-500/30">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-50 pointer-events-none" />
      <LandingNavbar />
      <main className="relative z-10">
        <LandingHero />
        <HowItWorks />
      </main>
    </div>
  );
};
