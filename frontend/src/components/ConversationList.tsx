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
          sortedConversations.map((chat) => {
            const website = state.websites.find(w => w.website_id === chat.website_id);
            const domainName = website ? (website.domain || website.source_url) : 'No website';

            return (
              <div
                key={chat.id}
                className={`flex items-start gap-2 px-3 py-2 rounded-lg transition-colors group cursor-pointer ${
                  chatId === chat.id 
                    ? 'bg-violet-500/10 text-violet-300' 
                    : 'hover:bg-white/5 text-slate-300'
                }`}
                onClick={() => navigate(`/workspace/chat/${chat.id}`)}
              >
                <MessageSquare className={`w-4 h-4 shrink-0 mt-1 ${chatId === chat.id ? 'text-violet-400' : 'text-slate-400'}`} />
                <div className="flex-1 min-w-0 flex flex-col">
                  <span className="text-sm font-medium truncate">
                    {chat.title}
                  </span>
                  <span className="text-[10px] text-slate-500 truncate mt-0.5">
                    {domainName}
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const remainingConversations = state.conversations.filter(c => c.id !== chat.id);
                    deleteConversation(chat.id);
                    if (chatId === chat.id) {
                      if (remainingConversations.length > 0) {
                        const nextChat = [...remainingConversations].sort((a, b) => 
                          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
                        )[0];
                        navigate(`/workspace/chat/${nextChat.id}`);
                      } else {
                        navigate('/workspace');
                      }
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 hover:text-rose-400 transition-opacity p-1 mt-0.5"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
