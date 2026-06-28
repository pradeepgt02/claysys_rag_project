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
  // Streaming progress fields (present in intermediate events)
  stage?: string;
  processed_chunks?: number;
  total_chunks?: number;
  percentage?: number;
  timings?: Record<string, number>;
}

export interface ChatRequest {
  website_id: string;
  question: string;
  top_k: number;
}

export interface Source {
  url?: string;
  source_url?: string;
  title: string;
  heading: string;
  score?: number;
  is_primary_answer_source?: boolean;
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
  generator?: string;
  is_grounded?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  created_at?: string;
  sources?: Source[];
  used_context_fallback?: boolean;
  generator?: string;
  is_grounded?: boolean;
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
  websiteId?: string;
  websiteDomain?: string;
  created_at: string;
  updated_at: string;
  createdAt?: string;
  updatedAt?: string;
  messages: ChatMessage[];
  legacy_mixed?: boolean;
}

export interface WorkspaceState {
  websites: IndexedWebsite[];
  conversations: ChatConversation[];
  selectedWebsiteId: string;
  selectedConversationId: string;
}

export interface IndexedPageInfo {
  url: string;
  title: string;
  chunks_count: number;
  status: string;
}

export interface IndexedPagesStats {
  pages_indexed: number;
  chunks_created: number;
  vectors_stored: number;
}

export interface IndexedPagesResponse {
  success: boolean;
  website_id: string;
  source_url: string;
  stats: IndexedPagesStats;
  pages: IndexedPageInfo[];
}

