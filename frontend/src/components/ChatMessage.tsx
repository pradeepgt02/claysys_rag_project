import React from 'react';
import { User, Sparkles, AlertTriangle, ExternalLink, FileText } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../types/webmind';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  // Helper to safely format simple line breaks and bold strings
  const formatText = (text: string) => {
    return text.split('\n').map((line, idx) => {
      // Basic bold formatting match (**text**)
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const content = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx} className="font-bold text-white">{part.slice(2, -2)}</strong>;
        }
        return part;
      });
      return <p key={idx} className={idx > 0 ? 'mt-2' : ''}>{content}</p>;
    });
  };

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} w-full`}>
      {/* Avatar (Left for Assistant, Right for User) */}
      {!isUser && (
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-600 flex items-center justify-center shrink-0 shadow-lg shadow-sky-500/20">
          <Sparkles className="w-4.5 h-4.5 text-white" />
        </div>
      )}

      {/* Message Bubble container */}
      <div className={`max-w-[85%] sm:max-w-[75%] space-y-3 ${isUser ? 'order-1' : 'order-2'}`}>
        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-gradient-to-tr from-blue-600 to-sky-600 text-white rounded-br-none border border-blue-500/20 shadow-sm'
              : 'bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800/80 text-slate-800 dark:text-slate-200 rounded-bl-none shadow-sm dark:shadow-none'
          }`}
        >
          {formatText(message.generator === 'retrieval_guard' ? 'No relevant information was found in this website.' : message.content)}
        </div>

        {/* Fallback Warning Alerts */}
        {!isUser && message.generator === 'groq-fallback' && (
          <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-600 dark:text-amber-350 font-medium max-w-lg">
            <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0" />
            <span>Primary AI is busy. Answer generated using backup AI.</span>
          </div>
        )}
        
        {!isUser && message.generator === 'extractive-fallback' && (
          <div className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-600 dark:text-red-400 font-medium max-w-lg">
            <AlertTriangle className="w-4 h-4 text-red-500 dark:text-red-400 shrink-0" />
            <span>AI generation is temporarily unavailable. Showing relevant indexed pages instead.</span>
          </div>
        )}

        {/* Sources Section (only for assistant and if sources are available) */}
        {!isUser && (message.is_grounded !== false || message.generator === 'extractive-fallback') && message.sources && message.sources.length > 0 && (
          <div className="space-y-2 pl-1">
            <h4 className="text-[10px] font-bold text-slate-600 dark:text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-sky-500 dark:text-sky-400" />
              Retrieved References
            </h4>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => {
                const targetUrl = source.source_url || source.url;
                const displayTitle = source.title && source.title.trim() !== "" ? source.title : targetUrl;
                return (
                  <a
                    key={index}
                    href={targetUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 dark:bg-slate-950/40 dark:hover:bg-slate-900 border border-slate-200 hover:border-sky-500/40 dark:border-slate-800/60 dark:hover:border-sky-500/40 rounded-xl text-xs text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-all cursor-pointer group shadow-sm"
                  >
                    <div className="max-w-[180px] sm:max-w-[240px] truncate">
                      {source.is_primary_answer_source && (
                        <span className="inline-block px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30 text-[9px] font-semibold mb-1">
                          Answer source
                        </span>
                      )}
                      <span className="font-semibold block truncate">
                        {displayTitle}
                      </span>
                      {source.heading && (
                        <span className="text-[10px] text-slate-500 block truncate">
                          Section: {source.heading}
                        </span>
                      )}
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600 dark:text-slate-500 dark:group-hover:text-sky-400 transition-colors shrink-0" />
                  </a>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center shrink-0 order-3">
          <User className="w-4.5 h-4.5 text-slate-600 dark:text-slate-300" />
        </div>
      )}
    </div>
  );
};
