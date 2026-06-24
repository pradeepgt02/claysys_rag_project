import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Globe, Database, HelpCircle, ShieldAlert } from 'lucide-react';
import { IndexedWebsite, ChatMessage as ChatMessageType } from '../types/webmind';
import { ChatMessage } from './ChatMessage';
import { EmptyState } from './EmptyState';

interface ChatWindowProps {
  currentWebsite: IndexedWebsite;
  messages: ChatMessageType[];
  onSendMessage: (question: string) => void;
  isLoading: boolean;
  error: string | null;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  currentWebsite,
  messages,
  onSendMessage,
  isLoading,
  error,
}) => {
  const [question, setQuestion] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSendMessage(question.trim());
    setQuestion('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/10 border-l border-slate-900/10">
      {/* Top Header info */}
      <header className="px-6 py-4 bg-slate-950/60 border-b border-slate-800/40 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl">
            <Globe className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white truncate max-w-[200px] sm:max-w-sm" title={currentWebsite.source_url}>
                {currentWebsite.source_url}
              </h2>
              <span className="shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                Indexed
              </span>
            </div>
            {/* Stats row */}
            <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
              <span>{currentWebsite.pages_crawled} pages</span>
              <span className="text-slate-500">•</span>
              <span>{currentWebsite.chunks_created} chunks</span>
              <span className="text-slate-500">•</span>
              <span>{currentWebsite.vector_count} vectors</span>
            </div>
          </div>
        </div>
      </header>

      {/* Message Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <EmptyState
            sourceUrl={currentWebsite.source_url}
            onSelectSampleQuestion={(q) => onSendMessage(q)}
          />
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Loading / Searching Bubble */}
            {isLoading && (
              <div className="flex gap-4 justify-start items-start w-full">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/20 animate-pulse">
                  <Database className="w-4.5 h-4.5 text-white" />
                </div>
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl rounded-bl-none p-4 text-sm text-indigo-300 flex items-center gap-3 max-w-sm">
                  <Loader2 className="w-4.5 h-4.5 text-indigo-400 animate-spin shrink-0" />
                  <span className="font-medium animate-pulse">Searching indexed website...</span>
                </div>
              </div>
            )}

            {/* Error Message inside chat */}
            {error && (
              <div className="flex gap-4 justify-start items-start w-full">
                <div className="w-9 h-9 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-4.5 h-4.5 text-rose-400" />
                </div>
                <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl rounded-bl-none p-4 text-xs text-rose-300 max-w-md leading-relaxed">
                  <span className="font-semibold text-rose-200 block mb-1">Chat Error</span>
                  {error}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Bottom Input Area */}
      <footer className="p-4 sm:p-6 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative group">
          <div className="relative flex items-end bg-slate-950/60 border border-slate-800 focus-within:border-violet-500 rounded-2xl p-2 transition-all shadow-xl shadow-slate-950/20 focus-within:ring-2 focus-within:ring-violet-500/15">
            <textarea
              rows={1}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about the indexed content..."
              disabled={isLoading}
              className="flex-1 max-h-36 min-h-[44px] py-3 px-3 bg-transparent resize-none border-0 focus:ring-0 focus:outline-none text-slate-100 placeholder-slate-500 text-sm disabled:opacity-50"
              style={{ height: 'auto' }}
            />
             <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="p-3 bg-gradient-to-tr from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white rounded-xl transition-all shadow-lg hover:shadow-indigo-500/15 disabled:shadow-none flex items-center justify-center shrink-0 mb-0.5 mr-0.5 active:scale-95"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="flex justify-between px-3 pt-2 text-[10px] text-slate-500">
            <span>Shift + Enter for new line</span>
            <span>Enter to send</span>
          </div>
        </form>
      </footer>
    </div>
  );
};
