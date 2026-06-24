import React, { useState } from 'react';
import { Globe, HelpCircle, ArrowRight, Settings, AlertTriangle } from 'lucide-react';

interface UrlIngestionCardProps {
  onIngest: (url: string, maxPages: number, initialQuestion: string) => void;
  isLoading: boolean;
  error: string | null;
}

export const UrlIngestionCard: React.FC<UrlIngestionCardProps> = ({ onIngest, isLoading, error }) => {
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState<number>(5);
  const [initialQuestion, setInitialQuestion] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Simple URL validation
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setValidationError('Please enter a website URL');
      return;
    }

    try {
      // Validate protocol
      if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
        setValidationError('URL must start with http:// or https://');
        return;
      }
      new URL(trimmedUrl);
    } catch (_) {
      setValidationError('Please enter a valid absolute URL (e.g., https://example.com)');
      return;
    }

    onIngest(trimmedUrl, maxPages, initialQuestion.trim());
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 md:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
      {/* Background glowing effects */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-violet-600/10 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-600/10 rounded-full blur-3xl -z-10 pointer-events-none" />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* URL Input */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Globe className="w-4 h-4 text-violet-400" />
            Website URL
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-violet-400 transition-colors">
              <Globe className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              disabled={isLoading}
              className="w-full pl-12 pr-4 py-4 bg-slate-950/50 border border-slate-800 group-hover:border-slate-700 focus:border-violet-500 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20 transition-all text-base disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
        </div>

        {/* Optional Initial Question */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-indigo-400" />
            <span>Initial Question <span className="text-xs text-slate-500 font-normal">(Optional)</span></span>
          </label>
          <input
            type="text"
            value={initialQuestion}
            onChange={(e) => setInitialQuestion(e.target.value)}
            placeholder="How do I get started? / What is this website about?"
            disabled={isLoading}
            className="w-full px-4 py-3.5 bg-slate-950/50 border border-slate-800 hover:border-slate-700 focus:border-indigo-500 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Advanced Settings Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <Settings className="w-3.5 h-3.5 text-slate-500" />
            <span>Crawling Limits</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Max pages:</span>
            <div className="inline-flex p-1 bg-slate-950/80 border border-slate-800 rounded-xl">
              {[1, 3, 5, 10].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setMaxPages(num)}
                  disabled={isLoading}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    maxPages === num
                      ? 'bg-violet-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  } disabled:opacity-50`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Local validation or Server errors */}
        {(validationError || error) && (
          <div className="flex items-start gap-3 p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-sm text-rose-300">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-rose-200">Error Occurred</span>
              <p className="text-xs text-rose-300/90 leading-relaxed">
                {validationError || error}
              </p>
            </div>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-violet-600 via-indigo-600 to-indigo-700 hover:from-violet-500 hover:to-indigo-500 text-white font-bold rounded-2xl shadow-xl shadow-indigo-500/10 transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-60 disabled:pointer-events-none"
        >
          <span>Index Website</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        {/* Helper info */}
        <p className="text-[11px] text-center text-slate-500 leading-relaxed max-w-lg mx-auto">
          Supports static websites, dynamic JavaScript websites, PDFs, JSON APIs, documentation sites, blogs, and e-commerce pages.
        </p>
      </form>
    </div>
  );
};
