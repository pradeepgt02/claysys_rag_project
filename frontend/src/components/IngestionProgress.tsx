import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, ShieldAlert } from 'lucide-react';

interface IngestionProgressProps {
  url: string;
}

const INGESTION_STEPS = [
  'Validating URL and checking constraints',
  'Detecting content type and accessibility',
  'Crawling relevant pages on the website domain',
  'Extracting relevant text and heading content',
  'Generating vector embeddings for chunks',
  'Building the local FAISS search index'
];

export const IngestionProgress: React.FC<IngestionProgressProps> = ({ url }) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    // Progressively cycle through steps to simulate background steps during API fetch
    const stepDuration = 3500; // 3.5s per step
    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < INGESTION_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, stepDuration);

    return () => clearInterval(interval);
  }, []);

  // Compute progress percentage
  const progressPercent = Math.min(((activeStep + 0.5) / INGESTION_STEPS.length) * 100, 95);

  return (
    <div className="w-full max-w-xl mx-auto bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 md:p-8 backdrop-blur-xl shadow-2xl space-y-6 text-center">
      {/* Title / Status */}
      <div className="space-y-2">
        <h3 className="text-lg font-bold text-white tracking-tight flex items-center justify-center gap-2">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          Ingesting Website
        </h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto truncate" title={url}>
          Processing: {url}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-900">
          <div
            className="h-full bg-gradient-to-r from-violet-600 via-indigo-500 to-cyan-500 transition-all duration-1000 ease-out rounded-full shadow-[0_0_8px_rgba(99,102,241,0.5)]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 font-semibold uppercase px-0.5">
          <span>Starting</span>
          <span>Indexing</span>
        </div>
      </div>

      {/* Steps List */}
      <div className="text-left space-y-3.5 pt-2">
        {INGESTION_STEPS.map((step, idx) => {
          const isCompleted = idx < activeStep;
          const isActive = idx === activeStep;

          return (
            <div
              key={idx}
              className={`flex items-start gap-3 transition-all duration-300 ${
                isActive ? 'opacity-100' : isCompleted ? 'opacity-60' : 'opacity-30'
              }`}
            >
              <div className="shrink-0 mt-0.5">
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500 font-bold bg-slate-950/20">
                    {idx + 1}
                  </div>
                )}
              </div>
              <div className="space-y-0.5">
                <p className={`text-xs font-semibold ${isActive ? 'text-indigo-200' : 'text-slate-300'}`}>
                  {step}
                </p>
                {isActive && (
                  <p className="text-[10px] text-slate-500 animate-pulse">
                    Please keep this window open...
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
