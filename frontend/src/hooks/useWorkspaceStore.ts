import { useState, useEffect, useCallback } from 'react';
import { WorkspaceState, IndexedWebsite, ChatConversation, ChatMessage } from '../types/webmind';
import { loadWorkspaceState, saveWorkspaceState } from '../utils/workspaceStorage';

// We use a singleton event target to synchronize state across components
class StoreEmitter extends EventTarget {}
const storeEmitter = new StoreEmitter();
const STORE_UPDATE_EVENT = 'STORE_UPDATE';

let globalState = loadWorkspaceState();

const setGlobalState = (newState: WorkspaceState) => {
  globalState = newState;
  saveWorkspaceState(globalState);
  storeEmitter.dispatchEvent(new Event(STORE_UPDATE_EVENT));
};

export const useWorkspaceStore = () => {
  const [state, setState] = useState<WorkspaceState>(globalState);

  useEffect(() => {
    const handleUpdate = () => setState(globalState);
    storeEmitter.addEventListener(STORE_UPDATE_EVENT, handleUpdate);
    
    // Handle storage events from other tabs
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'webmind_workspace_v1' && e.newValue) {
        try {
          globalState = JSON.parse(e.newValue);
          setState(globalState);
        } catch (err) {
          console.error('Error syncing storage across tabs:', err);
        }
      }
    };
    window.addEventListener('storage', handleStorage);
    
    return () => {
      storeEmitter.removeEventListener(STORE_UPDATE_EVENT, handleUpdate);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const addWebsite = useCallback((website: IndexedWebsite) => {
    setGlobalState({
      ...globalState,
      websites: [...globalState.websites.filter(w => w.website_id !== website.website_id), website],
      selectedWebsiteId: website.website_id,
    });
  }, []);

  const setSelectedWebsiteId = useCallback((id: string) => {
    setGlobalState({ ...globalState, selectedWebsiteId: id });
  }, []);

  const setSelectedConversationId = useCallback((id: string) => {
    setGlobalState({ ...globalState, selectedConversationId: id });
  }, []);

  const createConversation = useCallback((conversation: ChatConversation) => {
    setGlobalState({
      ...globalState,
      conversations: [...globalState.conversations, conversation],
      selectedConversationId: conversation.id,
      selectedWebsiteId: conversation.website_id || globalState.selectedWebsiteId,
    });
  }, []);

  const updateConversation = useCallback((id: string, updater: ((conv: ChatConversation) => ChatConversation) | Partial<ChatConversation>) => {
    setGlobalState({
      ...globalState,
      conversations: globalState.conversations.map(c => 
        c.id === id 
          ? (typeof updater === 'function' ? updater(c) : { ...c, ...updater }) 
          : c
      ),
    });
  }, []);

  const deleteConversation = useCallback((id: string) => {
    const newConvs = globalState.conversations.filter(c => c.id !== id);
    let newSelectedId = globalState.selectedConversationId;
    
    if (newSelectedId === id) {
      if (newConvs.length > 0) {
        // Select the most recently updated remaining conversation
        newSelectedId = [...newConvs].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0].id;
      } else {
        newSelectedId = '';
      }
    }

    setGlobalState({
      ...globalState,
      conversations: newConvs,
      selectedConversationId: newSelectedId,
    });
  }, []);

  const removeWebsite = useCallback((websiteId: string) => {
    setGlobalState({
      ...globalState,
      websites: globalState.websites.filter(w => w.website_id !== websiteId),
      selectedWebsiteId: globalState.selectedWebsiteId === websiteId ? '' : globalState.selectedWebsiteId,
    });
  }, []);

  return {
    state,
    addWebsite,
    removeWebsite,
    setSelectedWebsiteId,
    setSelectedConversationId,
    createConversation,
    updateConversation,
    deleteConversation,
  };
};
