import React, { useState, useRef, useEffect } from 'react';
import { Database, ChevronDown, Eye } from 'lucide-react';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

interface ChatHeaderProps {
  chatTitle: string;
  onWebsiteChange?: (newWebsiteId: string) => void;
  onViewIndexedPages?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ chatTitle, onWebsiteChange, onViewIndexedPages }) => {
  const { state } = useWorkspaceStore();
  const currentChat = state.conversations.find(c => c.id === state.selectedConversationId);
  const activeWebsiteId = currentChat?.website_id || state.selectedWebsiteId;
  const selectedWebsite = state.websites.find(w => w.website_id === activeWebsiteId);

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  return (
    <header className="h-16 border-b border-slate-200 dark:border-white/5 px-6 flex items-center justify-between shrink-0 bg-white/80 dark:bg-[#030712]/80 backdrop-blur-md sticky top-0 z-20">
      <div className="flex flex-col">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{chatTitle}</h2>
        {selectedWebsite ? (
          <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            {selectedWebsite.domain || selectedWebsite.source_url}
          </span>
        ) : (
          <span className="text-xs text-slate-500">No website selected</span>
        )}
      </div>

      <div className="flex items-center gap-3">
        {selectedWebsite && (
          <button
            onClick={onViewIndexedPages}
            className="flex items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 hover:border-blue-500/50 hover:bg-slate-50 dark:hover:bg-slate-950/60 rounded-xl px-4 py-2.5 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all cursor-pointer font-medium"
          >
            <Eye className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 shrink-0" />
            <span>View indexed pages</span>
          </button>
        )}

        <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 hover:border-blue-500/50 rounded-xl pl-3 pr-10 py-2.5 text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all cursor-pointer relative min-w-[220px] text-left hover:bg-slate-50 dark:hover:bg-slate-950/60 font-medium"
        >
          <Database className="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0" />
          <span className="truncate pr-2 select-none">
            {selectedWebsite ? (selectedWebsite.domain || selectedWebsite.source_url) : 'Select knowledge base...'}
          </span>
          <ChevronDown className={`w-4 h-4 text-slate-500 dark:text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 transition-transform duration-200 ${isOpen ? 'rotate-180 text-blue-600 dark:text-blue-400' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-64 bg-white/95 dark:bg-[#090d16]/95 border border-slate-200 dark:border-white/10 rounded-2xl shadow-2xl py-2 z-50 backdrop-blur-xl animate-fade-in flex flex-col gap-0.5 max-h-[300px] overflow-y-auto">
            <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider select-none">
              Knowledge Bases
            </div>
            
            {state.websites.length === 0 ? (
              <div className="px-3 py-2 text-xs text-slate-500 italic select-none">
                No databases indexed yet.
              </div>
            ) : (
              state.websites.map(w => {
                const isSelected = w.website_id === activeWebsiteId;
                return (
                  <button
                    key={w.website_id}
                    onClick={() => {
                      if (onWebsiteChange) {
                        onWebsiteChange(w.website_id);
                      }
                      setIsOpen(false);
                    }}
                    className={`flex items-center justify-between w-full text-left px-3 py-2.5 text-xs font-semibold transition-all rounded-xl mx-2 w-[calc(100%-16px)] ${
                      isSelected
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-white'
                    }`}
                  >
                    <span className="truncate">{w.domain || w.source_url}</span>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-500 dark:bg-blue-400 shrink-0 ml-2 animate-pulse" />}
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>
      </div>
    </header>
  );
};
