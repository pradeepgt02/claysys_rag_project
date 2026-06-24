import React from 'react';
import { Database, ChevronDown } from 'lucide-react';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

interface ChatHeaderProps {
  chatTitle: string;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ chatTitle }) => {
  const { state, setSelectedWebsiteId } = useWorkspaceStore();
  const selectedWebsite = state.websites.find(w => w.website_id === state.selectedWebsiteId);

  return (
    <header className="h-16 border-b border-white/5 px-6 flex items-center justify-between shrink-0 bg-[#030712]/80 backdrop-blur-md sticky top-0 z-20">
      <div className="flex flex-col">
        <h2 className="text-sm font-semibold text-slate-100">{chatTitle}</h2>
        {selectedWebsite ? (
          <span className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            {selectedWebsite.domain || selectedWebsite.source_url}
          </span>
        ) : (
          <span className="text-xs text-slate-500">No website selected</span>
        )}
      </div>

      <div className="relative group">
        <select
          value={state.selectedWebsiteId || ''}
          onChange={(e) => setSelectedWebsiteId(e.target.value)}
          className="appearance-none bg-slate-900 border border-white/10 rounded-lg pl-9 pr-10 py-2 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent cursor-pointer hover:bg-slate-800 transition-colors"
        >
          <option value="" disabled>Select knowledge base...</option>
          {state.websites.map(w => (
            <option key={w.website_id} value={w.website_id}>
              {w.domain || w.source_url}
            </option>
          ))}
        </select>
        <Database className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
    </header>
  );
};
