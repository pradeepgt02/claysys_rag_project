import React, { useState } from 'react';
import { Globe, Search, ArrowRight, Layers } from 'lucide-react';

interface AddWebsiteFormProps {
  onIngest: (url: string, maxPages: number, initialQuestion: string) => void;
  isLoading: boolean;
  error: string | null;
}

export const AddWebsiteForm: React.FC<AddWebsiteFormProps> = ({ onIngest, isLoading, error }) => {
  const [url, setUrl] = useState('');
  const [initialQuestion, setInitialQuestion] = useState('');
  const [maxPages, setMaxPages] = useState(25);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onIngest(url.trim(), maxPages, initialQuestion.trim());
  };

  const getWarningText = (pages: number) => {
    if (pages <= 10) return "Fast indexing. Best for quick demos and small websites.";
    if (pages === 25) return "Recommended balance between coverage and indexing time.";
    if (pages === 50) return "May take several minutes and use more embedding API quota.";
    if (pages === 100) return "Large crawl. May take longer and consume significant embedding API quota.";
    return "";
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Add a website</h2>
        <p className="text-slate-400">Create a private knowledge base from any public website.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
        <div className="space-y-5">
          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Website URL</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                <Globe className="h-5 w-5 text-slate-500" />
              </div>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                required
                className="w-full pl-11 pr-4 py-3 bg-slate-950 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-100 placeholder-slate-500 transition-all"
              />
            </div>
          </div>

          {/* Initial Question Input */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Initial Question (Optional)</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-500" />
              </div>
              <input
                type="text"
                value={initialQuestion}
                onChange={(e) => setInitialQuestion(e.target.value)}
                placeholder="What is this website about?"
                className="w-full pl-11 pr-4 py-3 bg-slate-950 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-100 placeholder-slate-500 transition-all"
              />
            </div>
          </div>

          {/* Max Pages Dropdown */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Max Pages to Crawl</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                <Layers className="h-5 w-5 text-slate-500" />
              </div>
              <select
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full pl-11 pr-4 py-3 bg-slate-950 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-slate-100 appearance-none transition-all"
              >
                <option value={1}>1 page — Quick test</option>
                <option value={3}>3 pages — Small</option>
                <option value={5}>5 pages — Basic</option>
                <option value={10}>10 pages — Standard</option>
                <option value={25}>25 pages — Recommended</option>
                <option value={50}>50 pages — Documentation</option>
                <option value={100}>100 pages — Large website</option>
              </select>
            </div>
            <p className="mt-2 text-xs text-slate-400">
              {getWarningText(maxPages)}
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-colors"
          >
            {isLoading ? 'Processing...' : 'Crawl and index website'}
            {!isLoading && <ArrowRight className="w-5 h-5" />}
          </button>
        </div>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500 leading-relaxed">
        Supports static websites, JavaScript-rendered websites, PDFs, JSON APIs, documentation sites, blogs, and e-commerce pages.
      </p>
    </div>
  );
};
