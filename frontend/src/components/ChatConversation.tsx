import React, { useEffect, useRef } from 'react';
import { ChatMessage as ChatMessageType, IndexedWebsite } from '../types/webmind';
import { ChatMessage } from './ChatMessage';
import { Sparkles, Loader2 } from 'lucide-react';

interface ChatConversationProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  selectedWebsite: IndexedWebsite | undefined;
}

export const ChatConversation: React.FC<ChatConversationProps> = ({ messages, isLoading, selectedWebsite }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 custom-scrollbar">
      <div className="max-w-4xl mx-auto w-full flex flex-col gap-6">
        {selectedWebsite && messages.length === 0 && (
          <div className="flex gap-4 justify-start w-full">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-600 flex items-center justify-center shrink-0 shadow-lg shadow-sky-500/20">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <div className="max-w-[85%] sm:max-w-[75%] space-y-3">
              <div className="p-4 bg-slate-900/50 border border-slate-800/80 text-slate-200 rounded-2xl rounded-bl-none text-sm leading-relaxed">
                This website ({selectedWebsite.domain || selectedWebsite.source_url}) is indexed and ready. Ask anything about its content.
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex gap-4 justify-start w-full">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-600 flex items-center justify-center shrink-0 shadow-lg shadow-sky-500/20">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <div className="p-4 bg-slate-900/50 border border-slate-800/80 rounded-2xl rounded-bl-none flex items-center gap-3 min-w-[200px]">
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
              <span className="text-sm font-medium text-slate-400">Searching indexed website...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} className="h-4 shrink-0" />
      </div>
    </div>
  );
};
