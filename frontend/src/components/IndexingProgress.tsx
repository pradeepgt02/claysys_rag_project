import React from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

// Maps backend stage identifiers to ordered UI step definitions
const STAGE_ORDER = [
  "validating_url",
  "detecting_content_type",
  "crawling_pages",
  "extracting_content",
  "chunking_content",
  "creating_embeddings",
  "building_faiss_index",
  "saving_metadata",
  "completed",
];

const STAGE_LABELS: Record<string, string> = {
  validating_url: "Validating URL",
  detecting_content_type: "Detecting content type",
  crawling_pages: "Crawling relevant pages",
  extracting_content: "Extracting content",
  chunking_content: "Chunking content",
  creating_embeddings: "Creating embeddings",
  building_faiss_index: "Building FAISS index",
  saving_metadata: "Saving metadata",
  completed: "Completed",
};

interface IndexingProgressProps {
  url: string;
  maxPages?: number;
  /** Active backend stage key (e.g. "creating_embeddings") */
  activeStage?: string;
  /** Chunks processed so far (only meaningful during creating_embeddings) */
  processedChunks?: number;
  /** Total chunk count (only meaningful during creating_embeddings) */
  totalChunks?: number;
  /** 0-100 percentage (only meaningful during creating_embeddings) */
  percentage?: number;
}

export const IndexingProgress: React.FC<IndexingProgressProps> = ({
  url,
  maxPages,
  activeStage,
  processedChunks,
  totalChunks,
  percentage,
}) => {
  // Determine which step index is currently active
  const activeIndex = activeStage ? STAGE_ORDER.indexOf(activeStage) : 0;

  // Build the display steps (exclude 'completed' sentinel from list—it's used for the header)
  const displayStages = STAGE_ORDER.filter((s) => s !== "completed");
  const isDone = activeStage === "completed";

  const [elapsedTime, setElapsedTime] = React.useState(0);

  React.useEffect(() => {
    if (isDone) return;
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isDone]);

  const formatTime = (secs: number) => {
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}m ${remainingSecs}s`;
  };

  return (
    <div className="w-full max-w-md mx-auto bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-500/10 flex items-center justify-center mx-auto mb-4 border border-blue-200 dark:border-blue-500/20">
          {isDone ? (
            <CheckCircle2 className="w-8 h-8 text-emerald-500 dark:text-emerald-400" />
          ) : (
            <Loader2 className="w-8 h-8 text-blue-600 dark:text-blue-400 animate-spin" />
          )}
        </div>
        <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          {isDone
            ? 'Indexing complete!'
            : maxPages
            ? `Indexing up to ${maxPages} pages`
            : 'Indexing website'}
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 truncate px-4">{url}</p>
        
        <div className={`mt-3 inline-flex items-center gap-1.5 px-3 py-1 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-full text-xs font-semibold ${isDone ? 'text-emerald-700 dark:text-emerald-400' : 'text-blue-700 dark:text-blue-300'}`}>
          <span className={`w-2 h-2 rounded-full ${isDone ? 'bg-emerald-500' : 'bg-blue-600 dark:bg-blue-500 animate-pulse'}`} />
          <span>{isDone ? `Total Time: ${formatTime(elapsedTime)}` : `Estimated Time: ~${formatTime(Math.round((maxPages || 25) * 1.5))}`}</span>
        </div>

        {!isDone && (
          <p className="text-xs text-slate-500 mt-2">
            Actual pages indexed may be lower if the website has fewer relevant crawlable pages.
          </p>
        )}
      </div>

      <div className="space-y-4">
        {displayStages.map((stage) => {
          const stageIndex = STAGE_ORDER.indexOf(stage);
          const isCompleted = isDone || stageIndex < activeIndex;
          const isCurrent = !isDone && stage === activeStage;

          // Build label — append progress detail for embedding stage
          let label = STAGE_LABELS[stage] || stage;
          if (isCurrent && stage === "creating_embeddings" && totalChunks && totalChunks > 0) {
            label = `Creating embeddings (${processedChunks ?? 0} / ${totalChunks})`;
          }

          return (
            <div
              key={stage}
              className={`flex items-center gap-3 transition-opacity duration-300 ${
                isCompleted || isCurrent ? 'opacity-100' : 'opacity-40'
              }`}
            >
              <div className="shrink-0">
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-500" />
                ) : isCurrent ? (
                  <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-400 dark:text-slate-600" />
                )}
              </div>
              <span
                className={`text-sm font-medium ${
                  isCurrent
                    ? 'text-blue-700 dark:text-blue-300'
                    : isCompleted
                    ? 'text-slate-700 dark:text-slate-300'
                    : 'text-slate-400 dark:text-slate-500'
                }`}
              >
                {label}
              </span>

              {/* Inline progress bar for embedding stage */}
              {isCurrent && stage === "creating_embeddings" && percentage != null && percentage > 0 && (
                <div className="ml-auto shrink-0 w-20">
                  <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 dark:bg-blue-500 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
