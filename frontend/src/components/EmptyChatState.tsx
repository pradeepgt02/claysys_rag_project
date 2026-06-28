import React from 'react';
import { Globe, Plus, Sparkles, MessageSquare, HelpCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

interface EmptyChatStateProps {
  mode?: 'welcome' | 'active_chat';
  selectedWebsiteDomain?: string;
  onSelectQuestion?: (question: string) => void;
}

export const EmptyChatState: React.FC<EmptyChatStateProps> = ({
  mode = 'welcome',
  selectedWebsiteDomain = 'website',
  onSelectQuestion
}) => {
  const navigate = useNavigate();
  const { state, createConversation } = useWorkspaceStore();
  const hasWebsites = state.websites.length > 0;

  const handleNewChat = () => {
    const newChatId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
    const now = new Date().toISOString();
    const websiteId = state.selectedWebsiteId;
    const selectedWebsite = state.websites.find(w => w.website_id === websiteId);
    
    createConversation({
      id: newChatId,
      title: "New chat",
      website_id: websiteId,
      websiteId: websiteId,
      websiteDomain: selectedWebsite?.domain || selectedWebsite?.source_url || '',
      created_at: now,
      createdAt: now,
      updated_at: now,
      updatedAt: now,
      messages: []
    });

    navigate(`/workspace/chat/${newChatId}`);
  };

  if (mode === 'active_chat') {
    const exampleQuestions = [
      "What is this website about?",
      "What information is available here?",
      "Show the main topics on this website"
    ];

    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-xl mx-auto space-y-8 animate-fade-in select-none">
        <div className="space-y-3">
          <div className="w-16 h-16 bg-gradient-to-tr from-blue-600 to-sky-600 rounded-2xl flex items-center justify-center mx-auto shadow-xl shadow-sky-500/20">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-sky-800 to-blue-800 dark:from-white dark:via-sky-200 dark:to-blue-300 tracking-tight">
              New chat
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Ask questions about <span className="text-blue-600 dark:text-blue-400 font-semibold">{selectedWebsiteDomain}</span>
            </p>
          </div>
        </div>

        <div className="w-full space-y-3">
          <div className="flex items-center gap-2 justify-center text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Suggested Questions</span>
          </div>

          <div className="grid gap-2.5">
            {exampleQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectQuestion && onSelectQuestion(q)}
                className="w-full text-left px-5 py-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 dark:bg-slate-900/30 dark:hover:bg-slate-900/80 dark:border-slate-800/40 hover:border-blue-500/30 dark:hover:border-blue-500/30 rounded-2xl text-xs font-semibold text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-all duration-300 flex items-center justify-between group hover:scale-[1.01] hover:shadow-lg hover:shadow-blue-500/5 active:scale-[0.99]"
              >
                <span>{q}</span>
                <MessageSquare className="w-4 h-4 text-slate-400 group-hover:text-blue-500 dark:text-slate-500 dark:group-hover:text-blue-400 transition-colors shrink-0 ml-2" />
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Welcome Mode
  return (
    <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto animate-fade-in select-none">
      <div className="w-16 h-16 bg-blue-100 dark:bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-200 dark:border-blue-500/20 shadow-[0_0_40px_rgba(139,92,246,0.1)]">
        <Globe className="w-8 h-8 text-blue-600 dark:text-blue-400" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">Welcome to WebMind</h2>
      <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed text-sm">
        {hasWebsites 
          ? "Select a website knowledge base and ask questions with cited sources."
          : "Add a website to get started and create a private knowledge base."}
      </p>
      {hasWebsites ? (
        <button 
          onClick={handleNewChat}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="w-5 h-5" />
          Start a new chat
        </button>
      ) : (
        <button 
          onClick={() => navigate('/workspace/index')}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="w-5 h-5" />
          Add your first website
        </button>
      )}
    </div>
  );
};
