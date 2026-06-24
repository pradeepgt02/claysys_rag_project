import React from 'react';
import { Sparkles, Terminal, MessageSquare, Compass } from 'lucide-react';

interface EmptyStateProps {
  sourceUrl: string;
  onSelectSampleQuestion: (question: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ sourceUrl, onSelectSampleQuestion }) => {
  const sampleQuestions = [
    'What is the main purpose of this website?',
    'Provide a structured summary of the key sections.',
    'Are there any getting started guides or tutorials?',
    'What contact information or links are available?',
  ];

  return (
    <div className="w-full max-w-xl mx-auto py-8 px-4 text-center space-y-8 animate-fade-in">
      {/* Visual Header */}
      <div className="space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center mx-auto shadow-xl shadow-indigo-500/10">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-white tracking-tight">
            Index Created Successfully!
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto truncate" title={sourceUrl}>
            Ready to analyze: {sourceUrl}
          </p>
        </div>
      </div>

      {/* Assistant Welcome Card */}
      <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-5 text-sm text-slate-300 leading-relaxed text-left flex gap-3.5 max-w-md mx-auto">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center shrink-0 text-indigo-400">
          <Terminal className="w-4 h-4" />
        </div>
        <div>
          <span className="font-semibold text-slate-200 block mb-0.5">WebMind Assistant</span>
          <span>Your website is indexed. Ask me anything about its content.</span>
        </div>
      </div>

      {/* Suggestion Prompts */}
      <div className="space-y-3 max-w-md mx-auto">
        <div className="flex items-center gap-2 justify-center text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          <Compass className="w-3.5 h-3.5 text-slate-500" />
          <span>Quick Prompts</span>
        </div>

        <div className="grid gap-2.5">
          {sampleQuestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectSampleQuestion(q)}
              className="w-full text-left px-4 py-3 bg-slate-900/20 hover:bg-slate-900/60 border border-slate-800/50 hover:border-violet-500/30 rounded-xl text-xs text-slate-300 hover:text-white font-medium transition-all flex items-center justify-between group"
            >
              <span>{q}</span>
              <MessageSquare className="w-3.5 h-3.5 text-slate-500 group-hover:text-violet-400 transition-colors shrink-0 ml-2" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
