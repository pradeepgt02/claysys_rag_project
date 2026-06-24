import React from 'react';
import { BrainCircuit, Plus, Moon, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ConversationList } from './ConversationList';
import { KnowledgeBaseList } from './KnowledgeBaseList';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const AppSidebar: React.FC = () => {
  const navigate = useNavigate();
  const { state, createConversation } = useWorkspaceStore();

  const handleNewChat = () => {
    // Generate simple id
    const newChatId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
    const now = new Date().toISOString();
    
    createConversation({
      id: newChatId,
      title: "New chat",
      website_id: state.selectedWebsiteId,
      created_at: now,
      updated_at: now,
      messages: []
    });

    navigate(`/workspace/chat/${newChatId}`);
  };

  return (
    <aside className="w-72 border-r border-white/5 bg-[#030712] hidden md:flex flex-col h-full shrink-0">
      {/* Header */}
      <div className="p-4 flex items-center gap-2 cursor-pointer" onClick={() => navigate('/workspace')}>
        <div className="p-1.5 bg-violet-500/20 rounded-lg text-violet-400">
          <BrainCircuit className="w-5 h-5" />
        </div>
        <span className="text-lg font-bold tracking-tight text-slate-100">WebMind</span>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mt-2">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 bg-white text-slate-900 px-4 py-2.5 rounded-xl font-semibold hover:bg-slate-200 transition-colors shadow-sm"
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
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center text-sm font-bold text-white shrink-0">
            P
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-slate-200 truncate">Pradeep Kumar</div>
            <div className="text-xs text-slate-500 truncate">Free Plan</div>
          </div>
          <button className="text-slate-500 hover:text-slate-300 p-1 shrink-0">
            <Moon className="w-4 h-4" />
          </button>
          <button className="text-slate-500 hover:text-slate-300 p-1 shrink-0">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
