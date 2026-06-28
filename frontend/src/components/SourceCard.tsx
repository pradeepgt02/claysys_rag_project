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
      className="flex items-start justify-between gap-3 p-3.5 bg-white hover:bg-slate-50 dark:bg-slate-950/40 dark:hover:bg-slate-900 border border-slate-200 hover:border-blue-300 dark:border-slate-800/80 dark:hover:border-blue-500/40 rounded-xl transition-all group w-full shadow-sm dark:shadow-none"
    >
      <div className="flex gap-2.5 overflow-hidden">
        <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5 overflow-hidden">
          <span className="text-xs font-semibold text-slate-800 block truncate group-hover:text-slate-900 dark:text-slate-200 dark:group-hover:text-white">
            {source.title || 'Untitled Reference'}
          </span>
          <span className="text-[10px] text-slate-500 block truncate font-mono">
            {source.url}
          </span>
          {source.heading && (
            <span className="inline-block text-[9px] font-bold text-slate-600 bg-slate-100 dark:text-slate-400 dark:bg-slate-800/50 px-1.5 py-0.5 rounded uppercase tracking-wider">
              Section: {source.heading}
            </span>
          )}
        </div>
      </div>
      <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 dark:text-slate-500 dark:group-hover:text-blue-400 transition-colors shrink-0" />
    </a>
  );
};
