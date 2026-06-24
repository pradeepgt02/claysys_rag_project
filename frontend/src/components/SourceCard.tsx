import React from 'react';
import { ExternalLink, FileText } from 'lucide-react';
import { Source } from '../types/webmind';

interface SourceCardProps {
  source: Source;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start justify-between gap-3 p-3.5 bg-slate-950/40 hover:bg-slate-900 border border-slate-800/80 hover:border-violet-500/40 rounded-xl transition-all group w-full"
    >
      <div className="flex gap-2.5 overflow-hidden">
        <FileText className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5 overflow-hidden">
          <span className="text-xs font-semibold text-slate-200 block truncate group-hover:text-white">
            {source.title || 'Untitled Reference'}
          </span>
          <span className="text-[10px] text-slate-500 block truncate font-mono">
            {source.url}
          </span>
          {source.heading && (
            <span className="inline-block text-[9px] font-bold text-slate-400 bg-slate-800/50 px-1.5 py-0.5 rounded uppercase tracking-wider">
              Section: {source.heading}
            </span>
          )}
        </div>
      </div>
      <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-violet-400 transition-colors shrink-0" />
    </a>
  );
};
