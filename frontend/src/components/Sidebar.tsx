import React from 'react';
import { Brain, Plus, CheckCircle2, Loader2, FileText, Database, ShieldAlert } from 'lucide-react';
import { IndexedWebsite } from '../types/webmind';

interface SidebarProps {
  currentWebsite: IndexedWebsite | null;
  onNewWebsite: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentWebsite, onNewWebsite }) => {
  return (
    <aside className="w-full md:w-80 bg-slate-950/80 border-b md:border-b-0 md:border-r border-slate-800/60 p-6 flex flex-col h-full backdrop-blur-xl">
      {/* Header Logo */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-gradient-to-tr from-blue-600 to-sky-600 rounded-xl shadow-lg shadow-sky-500/20 animate-pulse">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-sky-200 to-blue-300">
            WebMind
          </h1>
          <p className="text-xs text-slate-400 font-medium tracking-wide">
            Website Intelligence
          </p>
        </div>
      </div>

      {/* New Website Action */}
      <button
        onClick={onNewWebsite}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-sm transition-all duration-300 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-500 hover:to-sky-500 text-white shadow-lg shadow-sky-500/10 hover:shadow-sky-500/20 border border-blue-500/20 hover:scale-[1.02] active:scale-[0.98] mb-8"
      >
        <Plus className="w-4 h-4" />
        New Website
      </button>

      {/* Main Content Area */}
      <div className="flex-1 space-y-6">
        {currentWebsite ? (
          <div className="bg-slate-900/40 border border-slate-800/50 rounded-2xl p-5 space-y-4 backdrop-blur-md">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-sky-400" />
              Indexed Content
            </h2>

            {/* URL details */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-500 uppercase font-semibold">Source URL</label>
              <div className="text-sm font-medium text-slate-200 truncate" title={currentWebsite.source_url}>
                {currentWebsite.source_url}
              </div>
            </div>

            {/* ID details */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-500 uppercase font-semibold">Website ID</label>
              <div className="text-xs font-mono text-slate-400 select-all truncate bg-slate-950/40 p-2 rounded-lg border border-slate-800/30">
                {currentWebsite.website_id}
              </div>
            </div>

            {/* Stats list */}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-800/30">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">Pages</span>
                <span className="text-lg font-bold text-white flex items-center gap-1.5 mt-0.5">
                  <FileText className="w-4 h-4 text-blue-400" />
                  {currentWebsite.pages_crawled}
                </span>
              </div>
              <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-800/30">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">Chunks</span>
                <span className="text-lg font-bold text-white flex items-center gap-1.5 mt-0.5">
                  <Database className="w-4 h-4 text-sky-400" />
                  {currentWebsite.chunks_created}
                </span>
              </div>
            </div>

            {/* Vector count */}
            <div className="flex justify-between items-center bg-slate-950/20 px-3 py-2.5 rounded-xl border border-slate-800/20 text-xs">
              <span className="text-slate-400">FAISS Index Size</span>
              <span className="font-semibold text-sky-300">
                {currentWebsite.vector_count} vectors
              </span>
            </div>

            {/* Status Badge */}
            <div className="pt-2">
              {currentWebsite.status === 'indexed' && (
                <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 py-2 px-3 rounded-xl text-xs font-medium">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>Index ready for Q&A</span>
                </div>
              )}
              {currentWebsite.status === 'processing' && (
                <div className="flex items-center gap-2 text-amber-400 bg-amber-500/10 border border-amber-500/20 py-2 px-3 rounded-xl text-xs font-medium animate-pulse">
                  <Loader2 className="w-4 h-4 shrink-0 animate-spin" />
                  <span>Ingestion in progress...</span>
                </div>
              )}
              {currentWebsite.status === 'failed' && (
                <div className="flex flex-col gap-1.5 text-rose-400 bg-rose-500/10 border border-rose-500/20 py-2 px-3 rounded-xl text-xs font-medium">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 shrink-0" />
                    <span>Ingestion failed</span>
                  </div>
                  {currentWebsite.error_message && (
                    <span className="text-[11px] text-rose-300/80 font-normal leading-relaxed">
                      {currentWebsite.error_message}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center border border-dashed border-slate-800/40 rounded-2xl p-6 bg-slate-900/10">
            <div className="text-center space-y-2">
              <Brain className="w-8 h-8 mx-auto text-slate-600" />
              <p className="text-xs text-slate-500">No active index</p>
              <p className="text-[10px] text-slate-600 max-w-[160px] mx-auto">
                Ingest a website to start chat analysis
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-slate-900 mt-auto text-center">
        <p className="text-[10px] text-slate-500 font-medium">
          Powered by <span className="text-slate-400">RAG + FAISS + Gemini</span>
        </p>
      </div>
    </aside>
  );
};
