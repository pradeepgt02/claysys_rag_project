import React, { useEffect, useState } from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface IndexingProgressProps {
  url: string;
  maxPages?: number;
}

const STEPS = [
  "Validating URL",
  "Detecting content type",
  "Crawling relevant pages",
  "Extracting content",
  "Creating embeddings",
  "Building FAISS index"
];

export const IndexingProgress: React.FC<IndexingProgressProps> = ({ url, maxPages }) => {
  const [currentStep, setCurrentStep] = useState(0);

  // Fake progress simulation for visual effect while backend works
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="w-full max-w-md mx-auto bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4 border border-violet-500/20">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
        </div>
        <h3 className="text-xl font-bold text-slate-100">
          {maxPages ? `Indexing up to ${maxPages} pages` : 'Indexing website'}
        </h3>
        <p className="text-sm text-slate-400 mt-2 truncate px-4">{url}</p>
        <p className="text-xs text-slate-500 mt-2">
          Actual pages indexed may be lower if the website has fewer relevant crawlable pages.
        </p>
      </div>

      <div className="space-y-4">
        {STEPS.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          
          return (
            <div key={step} className={`flex items-center gap-3 transition-opacity duration-300 ${isCompleted || isCurrent ? 'opacity-100' : 'opacity-40'}`}>
              <div className="shrink-0">
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                ) : isCurrent ? (
                  <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-600" />
                )}
              </div>
              <span className={`text-sm font-medium ${isCurrent ? 'text-violet-300' : isCompleted ? 'text-slate-300' : 'text-slate-500'}`}>
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
