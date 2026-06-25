import { IngestRequest, IngestResponse, ChatRequest, ChatResponse, IndexedPagesResponse } from '../types/webmind';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export const webmindApi = {
  /**
   * Triggers website ingestion
   */
  async ingest(data: IngestRequest): Promise<IngestResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        let errorMessage = 'An error occurred during indexing';
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
        throw new ApiError('Cannot connect to the backend server. Please verify the backend is running at http://127.0.0.1:8000 and CORS is configured.');
      }
      throw new ApiError(error.message || 'An unexpected error occurred while contacting the server.');
    }
  },

  /**
   * Sends a chat question to an indexed website
   */
  async chat(chatData: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
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
      const response = await fetch(`${API_BASE_URL}/websites/${websiteId}/indexed-pages`, {
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
  }
};
