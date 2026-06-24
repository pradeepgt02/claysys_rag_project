import React from 'react';
import { Globe, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const EmptyChatState: React.FC = () => {
  const navigate = useNavigate();
  const { state } = useWorkspaceStore();
  const hasWebsites = state.websites.length > 0;

  return (
    <div className="h-full flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 bg-violet-500/10 rounded-2xl flex items-center justify-center mb-6 border border-violet-500/20 shadow-[0_0_40px_rgba(139,92,246,0.1)]">
        <Globe className="w-8 h-8 text-violet-400" />
      </div>
      <h2 className="text-2xl font-bold text-slate-100 mb-2">Welcome to WebMind</h2>
      <p className="text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
        {hasWebsites 
          ? "Select a website knowledge base and ask questions with cited sources."
          : "Add a website to get started and create a private knowledge base."}
      </p>
      {!hasWebsites && (
        <button 
          onClick={() => navigate('/workspace/index')}
          className="flex items-center gap-2 px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white rounded-xl font-medium transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add your first website
        </button>
      )}
    </div>
  );
};
