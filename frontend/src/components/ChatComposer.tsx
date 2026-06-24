import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
  isLoading: boolean;
}

export const ChatComposer: React.FC<ChatComposerProps> = ({ onSend, disabled, isLoading }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || disabled || isLoading) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-[#030712] border-t border-white/5 w-full shrink-0">
      <div className="max-w-4xl mx-auto w-full relative flex items-end gap-2 bg-slate-900 border border-white/10 rounded-2xl p-2 focus-within:border-violet-500/50 focus-within:ring-1 focus-within:ring-violet-500/50 transition-all shadow-sm">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={disabled ? "Select a website to start chatting..." : "Ask a question about this website..."}
          className="flex-1 max-h-[200px] min-h-[44px] bg-transparent resize-none outline-none text-slate-200 placeholder-slate-500 py-3 px-3 leading-relaxed disabled:opacity-50"
          rows={1}
        />
        <button
          onClick={handleSend}
          disabled={disabled || isLoading || !input.trim()}
          className="w-11 h-11 shrink-0 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl flex items-center justify-center transition-colors mb-0.5"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </button>
      </div>
      <div className="text-center mt-2">
        <span className="text-[10px] text-slate-600 font-medium">
          WebMind uses AI. Responses may be inaccurate. Check citations.
        </span>
      </div>
    </div>
  );
};
