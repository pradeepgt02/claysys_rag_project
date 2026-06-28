import { IngestRequest, IngestResponse, ChatRequest, ChatResponse, IndexedPagesResponse } from '../types/webmind';

const API_URL = import.meta.env.VITE_API_URL || 'https://pradeep002-claysys-rag-project.hf.space';

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ProgressEvent {
  stage: string;
  message?: string;
  percentage?: number;
  processed_chunks?: number;
  total_chunks?: number;
}

export const webmindApi = {
  /**
   * Triggers website ingestion and streams real-time progress events.
   * onProgress is called for each intermediate NDJSON line.
   * Resolves with the final IngestResponse when ingestion completes.
   */
  async ingest(
    data: IngestRequest,
    onProgress?: (event: ProgressEvent) => void
  ): Promise<IngestResponse> {
    let response: Response;
    try {
      response = await fetch(`${API_URL}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error: any) {
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        throw new ApiError(`Cannot connect to the backend server at ${API_URL}. Please verify it is running and CORS is configured.`);
      }
      throw new ApiError(error.message || 'An unexpected error occurred while contacting the server.');
    }

    if (!response.ok) {
      let errorMessage = 'An error occurred during indexing';
      try {
        const errData = await response.json();
        errorMessage = errData.detail || errData.message || errorMessage;
      } catch {
        // ignore
      }
      throw new ApiError(errorMessage, response.status);
    }

    // Read the streamed NDJSON body line by line
    const reader = response.body?.getReader();
    if (!reader) {
      throw new ApiError('Response body is not readable as a stream.');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let lastEvent: any = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last (potentially incomplete) line in the buffer
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          const event = JSON.parse(trimmed);
          lastEvent = event;
          if (onProgress) {
            onProgress(event as ProgressEvent);
          }
        } catch {
          // Ignore malformed lines
        }
      }
    }

    // Process any remaining buffer content
    if (buffer.trim()) {
      try {
        const event = JSON.parse(buffer.trim());
        lastEvent = event;
        if (onProgress) {
          onProgress(event as ProgressEvent);
        }
      } catch {
        // Ignore
      }
    }

    if (!lastEvent || !lastEvent.success) {
      const errMsg = lastEvent?.message || 'Indexing failed with no valid response.';
      throw new ApiError(errMsg);
    }

    return lastEvent as IngestResponse;
  },

  /**
   * Sends a chat question to an indexed website
   */
  async chat(chatData: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatData),
      });

      let responseData: any = null;
      try {
        responseData = await response.json();
      } catch {
        // Ignore JSON parsing failure
      }

      if (responseData) {
        const isDisplayable = !!responseData.answer || responseData.used_context_fallback === true;
        if (isDisplayable) {
          return responseData as ChatResponse;
        }

        if (!response.ok) {
          const errorMessage = responseData.detail || responseData.message || 'An error occurred during chat';
          throw new ApiError(errorMessage, response.status);
        }
      }

      if (!response.ok) {
        throw new ApiError(`Request failed with status ${response.status}`, response.status);
      }

      return responseData;
    } catch (error: any) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        throw new ApiError('Lost connection to the backend server. Please verify the backend is running.');
      }
      throw new ApiError(error.message || 'An unexpected error occurred while contacting the server.');
    }
  },

  /**
   * Fetches pages that have been crawled and indexed for a website
   */
  async getIndexedPages(websiteId: string): Promise<IndexedPagesResponse> {
    try {
      const response = await fetch(`${API_URL}/websites/${websiteId}/indexed-pages`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        let errorMessage = 'An error occurred while fetching indexed pages';
        try {
          const errData = await response.json();
          errorMessage = errData.detail || errData.message || errorMessage;
        } catch {
          // ignore parsing error
        }
        throw new ApiError(errorMessage, response.status);
      }

      return await response.json();
    } catch (error: any) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        throw new ApiError('Cannot connect to the backend server. Please verify the backend is running.');
      }
      throw new ApiError(error.message || 'An unexpected error occurred while contacting the server.');
    }
  },

  /**
   * Deletes an indexed website from the backend
   */
  async deleteWebsite(websiteId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${API_URL}/websites/${websiteId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        let errorMessage = 'An error occurred while deleting the website';
        try {
          const errData = await response.json();
          errorMessage = errData.detail || errData.message || errorMessage;
        } catch {
          // ignore
        }
        throw new ApiError(errorMessage, response.status);
      }

      return await response.json();
    } catch (error: any) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        throw new ApiError('Cannot connect to the backend server. Please verify the backend is running.');
      }
      throw new ApiError(error.message || 'An unexpected error occurred while contacting the server.');
    }
  }
};
