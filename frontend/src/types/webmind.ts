export interface IngestRequest {
  url: string;
  max_pages: number;
  initial_question: string;
}

export interface VectorStoreStats {
  vector_count: number;
  dimension: number;
}

export interface IngestResponse {
  success: boolean;
  website_id: string;
  source_url: string;
  content_type: string;
  pages_crawled: number;
  documents_processed: number;
  chunks_created: number;
  chunks_embedded: number;
  chunks_failed: number;
  vector_store_stats: VectorStoreStats;
  message: string;
}

export interface ChatRequest {
  website_id: string;
  question: string;
  top_k: number;
}

export interface Source {
  url: string;
  title: string;
  heading: string;
}

export interface ChatResponse {
  success: boolean;
  website_id: string;
  question: string;
  answer?: string;
  sources?: Source[];
  retrieved_chunks_count?: number;
  used_context_fallback?: boolean;
  message?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  created_at?: string;
  sources?: Source[];
  used_context_fallback?: boolean;
}

export interface IndexedWebsite {
  website_id: string;
  source_url: string;
  domain?: string;
  pages_crawled: number;
  chunks_created: number;
  vector_count: number;
  status: 'processing' | 'indexed' | 'failed';
  error_message?: string;
  created_at?: string;
}

export interface ChatConversation {
  id: string;
  title: string;
  website_id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface WorkspaceState {
  websites: IndexedWebsite[];
  conversations: ChatConversation[];
  selectedWebsiteId: string;
  selectedConversationId: string;
}
