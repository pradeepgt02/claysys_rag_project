import React, { useState, useEffect } from 'react';
import { X, Search, CheckCircle2, ExternalLink, Loader2, ShieldAlert } from 'lucide-react';
import { webmindApi } from '../api/webmindApi';
import { IndexedPagesResponse } from '../types/webmind';

interface IndexedPagesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  websiteId: string;
  domain: string;
}

export const IndexedPagesDrawer: React.FC<IndexedPagesDrawerProps> = ({
  isOpen,
  onClose,
  websiteId,
  domain,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<IndexedPagesResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchIndexedPages = async () => {
      if (!websiteId) return;
      setLoading(true);
      setError(null);
      try {
        const response = await webmindApi.getIndexedPages(websiteId);
        setData(response);
      } catch (err: any) {
        setError(err.message || 'Failed to load indexed pages.');
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && websiteId) {
      fetchIndexedPages();
    }
  }, [isOpen, websiteId]);

  if (!isOpen) return null;

  // Filter pages based on search query
  const filteredPages = data?.pages.filter(page => 
    page.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    page.url.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end overflow-hidden">
      {/* Backdrop overlay */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />

      {/* Drawer content container */}
      <div className="relative w-full max-w-md bg-slate-50 dark:bg-[#090d16] border-l border-slate-200 dark:border-white/10 shadow-2xl flex flex-col h-full z-10 animate-slide-in">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-white/5 flex items-center justify-between shrink-0">
          <div className="min-w-0">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 truncate pr-2" title={`Indexed content — ${domain}`}>
              Indexed content — {domain}
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:bg-slate-900 dark:border-white/5 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 flex flex-col custom-scrollbar">
          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center space-y-3 py-12">
              <Loader2 className="w-8 h-8 text-blue-600 dark:text-blue-500 animate-spin" />
              <p className="text-sm text-slate-600 dark:text-slate-400">Fetching indexed pages...</p>
            </div>
          )}

          {error && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-3 py-12">
              <div className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 flex items-center justify-center text-rose-500 dark:text-rose-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <p className="text-sm font-semibold text-rose-600 dark:text-rose-400">Failed to load content</p>
              <p className="text-xs text-slate-500 max-w-xs">{error}</p>
            </div>
          )}

          {!loading && !error && data && (
            <>
              {/* Summary Chips */}
              <div className="flex flex-wrap gap-2 shrink-0">
                <div className="px-3 py-1.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/5 text-xs text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5 shadow-sm dark:shadow-none">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
                  {data.stats.pages_indexed} pages
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/5 text-xs text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5 shadow-sm dark:shadow-none">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  {data.stats.chunks_created} chunks
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/5 text-xs text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5 shadow-sm dark:shadow-none">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  {data.stats.vectors_stored} vectors
                </div>
              </div>

              {/* Search bar */}
              <div className="relative shrink-0">
                <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search indexed pages..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10 focus:border-blue-500/50 rounded-xl text-xs text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/10 transition-all shadow-sm dark:shadow-none"
                />
              </div>

              {/* Pages Cards List */}
              <div className="space-y-3 flex-1">
                {filteredPages.length === 0 ? (
                  <div className="text-center py-12 space-y-2">
                    <p className="text-xs text-slate-500 italic">
                      {data.pages.length === 0 
                        ? "No pages have been indexed for this website yet." 
                        : "No pages match your search."
                      }
                    </p>
                  </div>
                ) : (
                  filteredPages.map((page, idx) => (
                    <a
                      key={idx}
                      href={page.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-4 bg-white hover:bg-slate-50 dark:bg-slate-900/30 dark:hover:bg-slate-900/70 border border-slate-200 dark:border-white/5 hover:border-blue-300 dark:hover:border-blue-500/25 rounded-xl transition-all group shadow-sm dark:shadow-none"
                    >
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-500 shrink-0 mt-0.5" />
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="text-xs font-bold text-slate-800 group-hover:text-blue-600 dark:text-slate-200 dark:group-hover:text-blue-400 transition-colors line-clamp-1 leading-normal">
                              {page.title}
                            </h4>
                            <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300 transition-colors shrink-0 mt-0.5" />
                          </div>
                          <p className="text-[10px] text-slate-500 truncate" title={page.url}>
                            {page.url}
                          </p>
                          <div className="pt-1.5 flex items-center justify-between">
                            <span className="text-[10px] font-semibold text-sky-700 bg-sky-100 dark:text-sky-400 dark:bg-sky-500/10 px-2 py-0.5 rounded-md">
                              {page.chunks_count} chunks
                            </span>
                            <span className="text-[10px] text-slate-500 dark:text-slate-600 font-medium">
                              {page.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </a>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
