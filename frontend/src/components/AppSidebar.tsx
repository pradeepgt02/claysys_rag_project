import React, { useState, useEffect } from 'react';
import { BrainCircuit, Plus, Moon, Sun, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ConversationList } from './ConversationList';
import { KnowledgeBaseList } from './KnowledgeBaseList';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const AppSidebar: React.FC = () => {
  const navigate = useNavigate();
  const { state, createConversation } = useWorkspaceStore();
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    return true;
  });
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.theme = 'dark';
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.theme = 'light';
    }
  }, [isDark]);

  const handleNewChat = () => {
    // Generate simple id
    const newChatId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
    const now = new Date().toISOString();
    const websiteId = state.selectedWebsiteId;
    const selectedWeb = state.websites.find(w => w.website_id === websiteId);
    
    createConversation({
      id: newChatId,
      title: "New chat",
      website_id: websiteId,
      websiteId: websiteId,
      websiteDomain: selectedWeb?.domain || selectedWeb?.source_url || '',
      created_at: now,
      createdAt: now,
      updated_at: now,
      updatedAt: now,
      messages: []
    });

    navigate(`/workspace/chat/${newChatId}`);
  };

  const confirmLogout = () => {
    setIsLoggingOut(false);
    navigate('/');
  };

  const cancelLogout = () => {
    setIsLoggingOut(false);
  };

  const handleThemeToggle = () => {
    setIsDark(!isDark);
  };

  return (
    <>
      <aside className="w-72 border-r border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-dark-900 hidden md:flex flex-col h-full shrink-0">
        {/* Header */}
        <div className="p-4 flex items-center gap-2 cursor-pointer" onClick={() => navigate('/workspace')}>
          <div className="p-1.5 bg-blue-100 dark:bg-blue-500/20 rounded-lg text-blue-600 dark:text-blue-400">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">WebMind</span>
        </div>

        {/* New Chat Button */}
        <div className="px-4 mt-2">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-4 py-2.5 rounded-xl font-semibold hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4 shrink-0" />
            <span>New chat</span>
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto mt-4 pb-4">
          <ConversationList />
          <KnowledgeBaseList />
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold text-white shrink-0">
              P
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-200 truncate">Pradeep Kumar</div>
              <div className="text-xs text-slate-500 truncate">Free Plan</div>
            </div>
            <button 
              className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 p-1 shrink-0 transition-colors"
              onClick={handleThemeToggle}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
            <button 
              className="text-slate-400 hover:text-rose-500 dark:text-slate-500 dark:hover:text-rose-400 p-1 shrink-0 transition-colors"
              onClick={() => setIsLoggingOut(true)}
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Logout Confirmation Modal */}
      {isLoggingOut && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 max-w-sm w-full shadow-2xl animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">Log Out</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              Are you sure you want to log out of WebMind?
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
                onClick={cancelLogout}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-rose-600 hover:bg-rose-500 transition-colors shadow-lg shadow-rose-900/20"
                onClick={confirmLogout}
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
