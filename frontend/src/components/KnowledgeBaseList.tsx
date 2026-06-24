import React from 'react';
import { Database, CheckCircle2, Loader2, AlertCircle, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const KnowledgeBaseList: React.FC = () => {
  const navigate = useNavigate();
  const { state, setSelectedWebsiteId } = useWorkspaceStore();

  return (
    <div className="mt-6 flex flex-col gap-2">
      <div className="flex items-center justify-between px-4 group">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Knowledge Bases
        </span>
        <button
          onClick={() => navigate('/workspace/index')}
          className="text-slate-500 hover:text-slate-300 transition-opacity p-1"
          title="Add website"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
      <div className="flex flex-col gap-1 px-2">
        {state.websites.length === 0 ? (
          <div className="px-3 py-2 text-sm text-slate-500 italic">No websites indexed yet.</div>
        ) : (
          state.websites.map((site) => (
            <div
              key={site.website_id}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group ${
                state.selectedWebsiteId === site.website_id ? 'bg-white/5' : ''
              }`}
              onClick={() => {
                setSelectedWebsiteId(site.website_id);
              }}
            >
              <Database className={`w-4 h-4 transition-colors ${state.selectedWebsiteId === site.website_id ? 'text-violet-400' : 'text-slate-400 group-hover:text-violet-400'}`} />
              <span className="text-sm font-medium text-slate-300 truncate flex-1">
                {site.domain || site.source_url}
              </span>
              {site.status === 'indexed' && (
                <div className="w-2 h-2 rounded-full bg-emerald-500" title="Indexed" />
              )}
              {site.status === 'processing' && (
                <Loader2 className="w-3 h-3 text-amber-500 animate-spin" title="Processing" />
              )}
              {site.status === 'failed' && (
                <AlertCircle className="w-3 h-3 text-rose-500" title="Failed" />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
