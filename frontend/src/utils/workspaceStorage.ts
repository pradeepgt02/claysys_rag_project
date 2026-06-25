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
    let state: WorkspaceState;

    if (raw) {
      const parsed = JSON.parse(raw);
      if (process.env.NODE_ENV === 'development') {
        console.log('Loaded workspace state:', parsed);
      }
      state = {
        websites: Array.isArray(parsed.websites) ? parsed.websites : [],
        conversations: Array.isArray(parsed.conversations) ? parsed.conversations : [],
        selectedWebsiteId: typeof parsed.selectedWebsiteId === 'string' ? parsed.selectedWebsiteId : '',
        selectedConversationId: typeof parsed.selectedConversationId === 'string' ? parsed.selectedConversationId : '',
      };
    } else {
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
        state = newState;
      } else {
        state = getInitialState();
      }
    }

    // Perform validation and repair of website_ids
    let repaired = false;
    const websiteIds = new Set(state.websites.map(w => w.website_id));
    
    let activeSelectedWebsiteId = state.selectedWebsiteId;
    if (activeSelectedWebsiteId && !websiteIds.has(activeSelectedWebsiteId)) {
      activeSelectedWebsiteId = state.websites.length > 0 ? state.websites[0].website_id : '';
      repaired = true;
    }
    
    const getHostname = (urlStr: string) => {
      try {
        return new URL(urlStr).hostname.toLowerCase();
      } catch {
        return '';
      }
    };

    const repairedConversations = state.conversations.map(conv => {
      let updatedConv = conv;

      if (!conv.website_id || !websiteIds.has(conv.website_id)) {
        const fallbackId = activeSelectedWebsiteId || (state.websites.length > 0 ? state.websites[0].website_id : '');
        if (conv.website_id !== fallbackId) {
          repaired = true;
          updatedConv = {
            ...updatedConv,
            website_id: fallbackId
          };
        }
      }

      const website = state.websites.find(w => w.website_id === updatedConv.website_id);
      if (website && website.domain) {
        const selectedDomain = website.domain.toLowerCase();
        let hasMixed = false;

        for (const msg of updatedConv.messages) {
          if (msg.sources && msg.sources.length > 0) {
            for (const src of msg.sources) {
              if (src.url) {
                const hostname = getHostname(src.url);
                const isMatch = hostname === selectedDomain || hostname.endsWith('.' + selectedDomain);
                if (!isMatch) {
                  hasMixed = true;
                  break;
                }
              }
            }
          }
          if (hasMixed) break;
        }

        if (hasMixed && !updatedConv.legacy_mixed) {
          repaired = true;
          updatedConv = {
            ...updatedConv,
            legacy_mixed: true
          };
        }
      }

      return updatedConv;
    });

    const finalState = {
      ...state,
      selectedWebsiteId: activeSelectedWebsiteId,
      conversations: repairedConversations
    };

    if (repaired) {
      saveWorkspaceState(finalState);
    }

    return finalState;
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
