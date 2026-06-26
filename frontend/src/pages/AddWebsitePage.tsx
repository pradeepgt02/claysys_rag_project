import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AddWebsiteForm } from '../components/AddWebsiteForm';
import { IndexingProgress } from '../components/IndexingProgress';
import { webmindApi, ProgressEvent } from '../api/webmindApi';
import { IndexedWebsite, ChatConversation } from '../types/webmind';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';

export const AddWebsitePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addWebsite, createConversation } = useWorkspaceStore();
  const prefillUrl = location.state?.prefillUrl;

  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestionError, setIngestionError] = useState<string | null>(null);
  const [ingestingUrl, setIngestingUrl] = useState<string | null>(null);
  const [ingestingMaxPages, setIngestingMaxPages] = useState<number>(25);

  // Real-time progress state driven by backend NDJSON events
  const [activeStage, setActiveStage] = useState<string>('');
  const [processedChunks, setProcessedChunks] = useState<number>(0);
  const [totalChunks, setTotalChunks] = useState<number>(0);
  const [percentage, setPercentage] = useState<number>(0);

  const handleIngest = async (url: string, maxPages: number, initialQuestion: string) => {
    setIsIngesting(true);
    setIngestionError(null);
    setIngestingUrl(url);
    setIngestingMaxPages(maxPages);

    // Reset progress state
    setActiveStage('validating_url');
    setProcessedChunks(0);
    setTotalChunks(0);
    setPercentage(0);

    const handleProgress = (event: ProgressEvent) => {
      const stage = event.stage || '';
      setActiveStage(stage);

      if (stage === 'creating_embeddings') {
        setProcessedChunks(event.processed_chunks ?? 0);
        setTotalChunks(event.total_chunks ?? 0);
        setPercentage(event.percentage ?? 0);
      }
    };

    try {
      const res = await webmindApi.ingest(
        { url, max_pages: maxPages, initial_question: initialQuestion },
        handleProgress
      );

      if (res.success) {
        // Extract domain from URL
        let domain = url;
        try {
          domain = new URL(url).hostname;
        } catch {
          // fallback to url if invalid
        }

        const newWebsite: IndexedWebsite = {
          website_id: res.website_id,
          source_url: res.source_url,
          domain: domain,
          pages_crawled: res.pages_crawled,
          chunks_created: res.chunks_created,
          vector_count: res.vector_store_stats.vector_count,
          status: 'indexed',
          created_at: new Date().toISOString(),
        };

        addWebsite(newWebsite);

        // Helper for generating unique ID
        const generateId = () => {
          if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
          }
          return Math.random().toString(36).substring(2, 9);
        };

        const newChatId = generateId();
        const now = new Date().toISOString();
        const websiteId = res.website_id;

        // Create new chat
        const newChat: ChatConversation = {
          id: newChatId,
          title: 'New chat',
          website_id: websiteId,
          websiteId: websiteId,
          websiteDomain: domain,
          created_at: now,
          createdAt: now,
          updated_at: now,
          updatedAt: now,
          messages: []
        };

        createConversation(newChat);

        // Set to completed to show the total time to the user
        setActiveStage('completed');

        // Wait 3 seconds so the user can see the final progress and total time
        setTimeout(() => {
          setIsIngesting(false);
          navigate(`/workspace/chat/${newChatId}${initialQuestion ? `?initialQuestion=${encodeURIComponent(initialQuestion)}` : ''}`);
        }, 3000);
      } else {
        setIngestionError(res.message || 'Indexing failed with success indicator set to false.');
        setIsIngesting(false);
      }
    } catch (err: any) {
      setIngestionError(err.message || 'An error occurred during indexing. Verify the server is running.');
      setIsIngesting(false);
    }
  };

  return (
    <div className="h-full w-full flex flex-col justify-center items-center p-6 relative">
      {/* Background glowing gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-[300px] h-[300px] bg-sky-500/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full relative z-10">
        {isIngesting && ingestingUrl ? (
          <IndexingProgress
            url={ingestingUrl}
            maxPages={ingestingMaxPages}
            activeStage={activeStage}
            processedChunks={processedChunks}
            totalChunks={totalChunks}
            percentage={percentage}
          />
        ) : (
          <AddWebsiteForm
            onIngest={handleIngest}
            isLoading={isIngesting}
            error={ingestionError}
            prefillUrl={prefillUrl}
          />
        )}
      </div>
    </div>
  );
};
