import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ChatHeader } from '../components/ChatHeader';
import { EmptyChatState } from '../components/EmptyChatState';
import { ChatConversation as ChatConversationComponent } from '../components/ChatConversation';
import { ChatComposer } from '../components/ChatComposer';
import { webmindApi } from '../api/webmindApi';
import { ChatMessage, ChatConversation } from '../types/webmind';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const ChatPage: React.FC = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialQuestion = searchParams.get('initialQuestion');
  
  const { state, setSelectedConversationId, updateConversation, createConversation } = useWorkspaceStore();
  
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const currentChat = state.conversations.find(c => c.id === chatId);
  // Ensure selectedWebsiteId from state maps to the current chat if it has one, otherwise fall back to global selection
  const activeWebsiteId = currentChat?.website_id || state.selectedWebsiteId;
  const selectedWebsite = state.websites.find(w => w.website_id === activeWebsiteId);

  // Helper for generating unique ID
  const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return Math.random().toString(36).substring(2, 9);
  };

  useEffect(() => {
    if (!chatId) return;

    if (chatId === 'new') {
      // Create a real conversation right away to avoid "new" floating state
      const newChatId = generateId();
      const now = new Date().toISOString();
      const websiteId = searchParams.get('websiteId') || state.selectedWebsiteId;
      
      createConversation({
        id: newChatId,
        title: "New chat",
        website_id: websiteId,
        created_at: now,
        updated_at: now,
        messages: []
      });
      navigate(`/workspace/chat/${newChatId}`, { replace: true });
    } else {
      if (currentChat && state.selectedConversationId !== chatId) {
        setSelectedConversationId(chatId);
      } else if (!currentChat && state.conversations.length > 0) {
        // Wait until it's loaded, if not found and state is loaded, maybe it was deleted
        navigate('/workspace', { replace: true });
      }
    }
  }, [chatId, currentChat, state.selectedConversationId, state.selectedWebsiteId, state.conversations.length, navigate, createConversation, setSelectedConversationId, searchParams]);

  // Handle initial question auto-send
  useEffect(() => {
    if (initialQuestion && currentChat && currentChat.messages.length === 0 && !isChatting) {
      handleSendMessage(initialQuestion);
      navigate(`/workspace/chat/${currentChat.id}`, { replace: true });
    }
  }, [initialQuestion, currentChat]);

  const handleSendMessage = async (question: string) => {
    if (!selectedWebsite || !currentChat) return;

    setIsChatting(true);
    setChatError(null);

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      created_at: new Date().toISOString()
    };

    const newTitle = currentChat.title === 'New chat' 
      ? (question.length > 35 ? question.substring(0, 35) + '...' : question)
      : currentChat.title;

    updateConversation(currentChat.id, (conv) => ({
      ...conv,
      title: newTitle,
      updated_at: new Date().toISOString(),
      messages: [...conv.messages, userMsg],
      website_id: selectedWebsite.website_id // ensure it's bound
    }));

    try {
      const res = await webmindApi.chat({
        website_id: selectedWebsite.website_id,
        question,
        top_k: 5,
      });

      const isDisplayable = !!res.answer || res.used_context_fallback === true;

      if (isDisplayable) {
        const assistantMsg: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: res.answer || '',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          created_at: new Date().toISOString(),
          sources: res.sources,
          used_context_fallback: res.used_context_fallback,
        };
        
        updateConversation(currentChat.id, (conv) => ({
          ...conv,
          updated_at: new Date().toISOString(),
          messages: [...conv.messages, assistantMsg]
        }));
      } else {
        setChatError(res.message || 'Failed to generate a response from the AI.');
      }
    } catch (err: any) {
      setChatError(err.message || 'An error occurred while calling the chatbot API.');
    } finally {
      setIsChatting(false);
    }
  };

  if (!currentChat) return null; // let useEffect redirect or load

  return (
    <div className="flex flex-col h-full w-full relative">
      <ChatHeader chatTitle={currentChat.title} />
      
      {chatError && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-30 max-w-md w-full bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-3 rounded-xl shadow-2xl flex items-start gap-3 backdrop-blur-md">
          <span className="text-sm font-medium">{chatError}</span>
          <button onClick={() => setChatError(null)} className="ml-auto text-rose-400 hover:text-rose-300">
            &times;
          </button>
        </div>
      )}

      {currentChat.messages.length === 0 ? (
        <EmptyChatState />
      ) : (
        <ChatConversationComponent 
          messages={currentChat.messages}
          isLoading={isChatting}
          selectedWebsite={selectedWebsite}
        />
      )}

      <ChatComposer 
        onSend={handleSendMessage}
        disabled={!selectedWebsite || state.websites.length === 0}
        isLoading={isChatting}
      />
    </div>
  );
};
