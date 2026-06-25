import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ChatHeader } from '../components/ChatHeader';
import { EmptyChatState } from '../components/EmptyChatState';
import { ChatConversation as ChatConversationComponent } from '../components/ChatConversation';
import { ChatComposer } from '../components/ChatComposer';
import { webmindApi } from '../api/webmindApi';
import { ChatMessage, ChatConversation } from '../types/webmind';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';
import { IndexedPagesDrawer } from '../components/IndexedPagesDrawer';

export const ChatPage: React.FC = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialQuestion = searchParams.get('initialQuestion');
  
  const { state, setSelectedConversationId, updateConversation, createConversation, setSelectedWebsiteId } = useWorkspaceStore();
  
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const currentChat = useMemo(() => {
    return state.conversations.find(c => c.id === chatId);
  }, [state.conversations, chatId]);

  const activeWebsiteId = currentChat?.website_id;

  const selectedWebsite = useMemo(() => {
    return state.websites.find(w => w.website_id === activeWebsiteId);
  }, [state.websites, activeWebsiteId]);

  // Helper for generating unique ID
  const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return Math.random().toString(36).substring(2, 9);
  };

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const handleWebsiteChange = (newWebsiteId: string) => {
    if (!currentChat) return;

    const hasMessages = currentChat.messages.length > 0;
    const newWebsite = state.websites.find(w => w.website_id === newWebsiteId);

    if (!hasMessages) {
      // Case A: Current conversation has zero messages
      updateConversation(currentChat.id, {
        website_id: newWebsiteId,
        websiteId: newWebsiteId,
        websiteDomain: newWebsite?.domain || newWebsite?.source_url || '',
        updated_at: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      });
      setSelectedWebsiteId(newWebsiteId);
    } else {
      // Case B: Current conversation has one or more messages
      const newChatId = generateId();
      const now = new Date().toISOString();

      createConversation({
        id: newChatId,
        title: "New chat",
        website_id: newWebsiteId,
        websiteId: newWebsiteId,
        websiteDomain: newWebsite?.domain || newWebsite?.source_url || '',
        created_at: now,
        createdAt: now,
        updated_at: now,
        updatedAt: now,
        messages: []
      });

      setSelectedWebsiteId(newWebsiteId);
      
      // Navigate to the new chat
      navigate(`/workspace/chat/${newChatId}`);

      // Show toast
      const domainName = newWebsite ? (newWebsite.domain || newWebsite.source_url) : 'website';
      showToast(`Started a new chat for ${domainName} to keep conversations separate.`);
    }
  };

  useEffect(() => {
    if (!chatId) return;

    if (chatId === 'new') {
      // Create a real conversation right away to avoid "new" floating state
      const newChatId = generateId();
      const now = new Date().toISOString();
      const websiteId = searchParams.get('websiteId') || state.selectedWebsiteId;
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
      navigate(`/workspace/chat/${newChatId}`, { replace: true });
    } else {
      if (currentChat && state.selectedConversationId !== chatId) {
        setSelectedConversationId(chatId);
      } else if (!currentChat && state.conversations.length > 0) {
        // If the current chat is not found (e.g., deleted), navigate to the most recently updated remaining chat
        const sorted = [...state.conversations].sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
        navigate(`/workspace/chat/${sorted[0].id}`, { replace: true });
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
    // Derive active conversation fresh
    const activeConversation = state.conversations.find(c => c.id === chatId);
    const activeWebsiteId = activeConversation?.website_id;

    if (!activeWebsiteId) {
      setChatError("Please select a website knowledge base first.");
      return;
    }

    if (activeConversation?.legacy_mixed) {
      return;
    }

    const selectedWebsite = state.websites.find(w => w.website_id === activeWebsiteId);
    if (!selectedWebsite) {
      setChatError("Please select a website knowledge base first.");
      return;
    }

    setIsChatting(true);
    setChatError(null);

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      created_at: new Date().toISOString()
    };

    const newTitle = activeConversation.title === 'New chat' 
      ? (question.length > 35 ? question.substring(0, 35) + '...' : question)
      : activeConversation.title;

    updateConversation(activeConversation.id, (conv) => ({
      ...conv,
      title: newTitle,
      updated_at: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: [...conv.messages, userMsg],
      website_id: activeWebsiteId,
      websiteId: activeWebsiteId,
      websiteDomain: selectedWebsite?.domain || selectedWebsite?.source_url || ''
    }));

    // Log chat index check debug information before calling API
    console.log("CHAT INDEX CHECK", {
      conversationId: activeConversation.id,
      websiteId: activeConversation.website_id,
      websiteDomain: selectedWebsite.domain || selectedWebsite.source_url,
      messageCount: activeConversation.messages.length
    });

    // Log chat request debug information
    console.log("CHAT REQUEST DEBUG", {
      conversationId: activeConversation.id,
      conversationWebsiteId: activeConversation.website_id,
      selectedWebsiteId: state.selectedWebsiteId,
      selectedWebsiteDomain: selectedWebsite?.domain,
      question
    });

    try {
      const res = await webmindApi.chat({
        website_id: activeWebsiteId,
        question,
        top_k: 5,
      });

      // Log chat response debug information
      console.log("CHAT RESPONSE DEBUG", {
        requestedWebsiteId: activeWebsiteId,
        sources: res.sources
      });

      // Source validation in frontend
      const getHostname = (urlStr: string) => {
        try {
          return new URL(urlStr).hostname.toLowerCase();
        } catch {
          return '';
        }
      };

      const selectedDomain = (selectedWebsite.domain || '').toLowerCase();
      let hasMismatch = false;

      if (res.sources && res.sources.length > 0) {
        for (const src of res.sources) {
          if (src.url) {
            const hostname = getHostname(src.url);
            const isMatch = hostname === selectedDomain || hostname.endsWith('.' + selectedDomain);
            if (!isMatch) {
              hasMismatch = true;
              break;
            }
          }
        }
      }

      if (hasMismatch) {
        console.warn("Safety check failed: Response sources do not match selected website domain", res);
        setChatError("Safety check: retrieved sources do not belong to the selected website. Please retry.");
        return;
      }

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
        
        updateConversation(activeConversation.id, (conv) => ({
          ...conv,
          updated_at: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
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
      <ChatHeader 
        chatTitle={currentChat.title} 
        onWebsiteChange={handleWebsiteChange} 
        onViewIndexedPages={() => setIsDrawerOpen(true)}
      />

      {import.meta.env.DEV && currentChat && (
        <div className="bg-slate-900 border-b border-white/5 px-6 py-1 text-[10px] text-slate-500 font-mono shrink-0 select-none">
          Active Index: {currentChat.website_id || 'None'}
        </div>
      )}

      {currentChat.legacy_mixed && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 text-amber-400 text-xs flex items-center justify-between shrink-0 font-medium select-none text-center">
          <span>This is an older mixed-source conversation. Create a new chat for clean website-specific answers.</span>
        </div>
      )}
      
      {toast && (
        <div className="absolute top-20 right-6 z-40 bg-violet-600 border border-violet-500 text-white px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-md text-xs font-semibold animate-fade-in transition-all duration-300">
          {toast}
        </div>
      )}

      {chatError && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-30 max-w-md w-full bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-3 rounded-xl shadow-2xl flex items-start gap-3 backdrop-blur-md">
          <span className="text-sm font-medium">{chatError}</span>
          <button onClick={() => setChatError(null)} className="ml-auto text-rose-400 hover:text-rose-300">
            &times;
          </button>
        </div>
      )}

      {currentChat.messages.length === 0 ? (
        <EmptyChatState 
          mode="active_chat"
          selectedWebsiteDomain={selectedWebsite?.domain || selectedWebsite?.source_url || 'website'}
          onSelectQuestion={handleSendMessage}
        />
      ) : (
        <ChatConversationComponent 
          messages={currentChat.messages}
          isLoading={isChatting}
          selectedWebsite={selectedWebsite}
        />
      )}

      {currentChat.legacy_mixed ? (
        <div className="p-4 bg-[#030712] border-t border-white/5 w-full shrink-0 flex items-center justify-center select-none animate-fade-in">
          <div className="text-center py-2.5 px-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl text-xs font-medium">
            This conversation is legacy and contains mixed sources. Please click "New chat" to ask questions.
          </div>
        </div>
      ) : (
        <ChatComposer 
          key={chatId}
          onSend={handleSendMessage}
          disabled={!selectedWebsite || state.websites.length === 0}
          isLoading={isChatting}
        />
      )}

      {selectedWebsite && (
        <IndexedPagesDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          websiteId={selectedWebsite.website_id}
          domain={selectedWebsite.domain || selectedWebsite.source_url}
        />
      )}
    </div>
  );
};
