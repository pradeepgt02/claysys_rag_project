import React from 'react';
import { MessageSquare, Trash2 } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const ConversationList: React.FC = () => {
  const navigate = useNavigate();
  const { chatId } = useParams<{ chatId: string }>();
  const { state, deleteConversation } = useWorkspaceStore();

  const sortedConversations = [...state.conversations].sort((a, b) => 
    new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );

  return (
    <div className="mt-4 flex flex-col gap-2">
      <div className="px-4">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Conversations
        </span>
      </div>
      <div className="flex flex-col gap-1 px-2 overflow-y-auto">
        {sortedConversations.length === 0 ? (
          <div className="px-3 py-2 text-sm text-slate-500 italic">No conversations yet.</div>
        ) : (
          sortedConversations.map((chat) => (
            <div
              key={chat.id}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors group cursor-pointer ${
                chatId === chat.id 
                  ? 'bg-violet-500/10 text-violet-300' 
                  : 'hover:bg-white/5 text-slate-300'
              }`}
              onClick={() => navigate(`/workspace/chat/${chat.id}`)}
            >
              <MessageSquare className={`w-4 h-4 shrink-0 ${chatId === chat.id ? 'text-violet-400' : 'text-slate-400'}`} />
              <span className="text-sm font-medium truncate flex-1">
                {chat.title}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(chat.id);
                  if (chatId === chat.id) {
                    navigate('/workspace');
                  }
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-rose-400 transition-opacity p-1"
                title="Delete chat"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
