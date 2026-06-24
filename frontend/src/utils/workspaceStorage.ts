import { WorkspaceState, IndexedWebsite, ChatConversation } from '../types/webmind';

const STORAGE_KEY = 'webmind_workspace_v1';

const getInitialState = (): WorkspaceState => ({
  websites: [],
  conversations: [],
  selectedWebsiteId: '',
  selectedConversationId: '',
});

export const loadWorkspaceState = (): WorkspaceState => {
  if (typeof window === 'undefined') return getInitialState();

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (process.env.NODE_ENV === 'development') {
        console.log('Loaded workspace state:', parsed);
      }
      return {
        websites: Array.isArray(parsed.websites) ? parsed.websites : [],
        conversations: Array.isArray(parsed.conversations) ? parsed.conversations : [],
        selectedWebsiteId: typeof parsed.selectedWebsiteId === 'string' ? parsed.selectedWebsiteId : '',
        selectedConversationId: typeof parsed.selectedConversationId === 'string' ? parsed.selectedConversationId : '',
      };
    }

    // Migration logic for old keys
    const oldWebsitesRaw = localStorage.getItem('indexed_websites');
    const oldConvsRaw = localStorage.getItem('chat_conversations');
    
    let migrated = false;
    let websites: IndexedWebsite[] = [];
    let conversations: ChatConversation[] = [];

    if (oldWebsitesRaw) {
      try {
        websites = JSON.parse(oldWebsitesRaw);
        migrated = true;
      } catch (e) {}
    }
    
    if (oldConvsRaw) {
      try {
        conversations = JSON.parse(oldConvsRaw);
        migrated = true;
      } catch (e) {}
    }

    if (migrated) {
      const newState: WorkspaceState = {
        websites,
        conversations,
        selectedWebsiteId: websites.length > 0 ? websites[0].website_id : '',
        selectedConversationId: conversations.length > 0 ? conversations[0].id : '',
      };
      saveWorkspaceState(newState);
      // Clean up old
      localStorage.removeItem('indexed_websites');
      localStorage.removeItem('chat_conversations');
      localStorage.removeItem('webmind_website');
      localStorage.removeItem('webmind_messages');
      return newState;
    }

    return getInitialState();
  } catch (error) {
    console.warn('Failed to load workspace state from localStorage', error);
    return getInitialState();
  }
};

export const saveWorkspaceState = (state: WorkspaceState): void => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    if (process.env.NODE_ENV === 'development') {
      console.log('Saved workspace state:', state);
    }
  } catch (error) {
    console.warn('Failed to save workspace state to localStorage', error);
  }
};
