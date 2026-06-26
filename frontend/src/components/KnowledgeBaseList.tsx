import React, { useState } from 'react';
import { Database, CheckCircle2, Loader2, AlertCircle, Plus, Trash2, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';
import { webmindApi } from '../api/webmindApi';
import { IndexedWebsite } from '../types/webmind';

export const KnowledgeBaseList: React.FC = () => {
  const navigate = useNavigate();
  const { state, setSelectedWebsiteId, removeWebsite } = useWorkspaceStore();
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [websiteToDelete, setWebsiteToDelete] = useState<IndexedWebsite | null>(null);

  const confirmDelete = async () => {
    if (!websiteToDelete) return;
    const websiteId = websiteToDelete.website_id;
    setIsDeleting(websiteId);
    setWebsiteToDelete(null);
    try {
      const res = await webmindApi.deleteWebsite(websiteId);
      if (res.success) {
        removeWebsite(websiteId);
      } else {
        alert('Failed to delete website: ' + res.message);
      }
    } catch (err: any) {
      alert('An error occurred while deleting: ' + err.message);
    } finally {
      setIsDeleting(null);
    }
  };

  const cancelDelete = () => setWebsiteToDelete(null);

  const handleDeleteClick = (site: IndexedWebsite, e: React.MouseEvent) => {
    e.stopPropagation();
    setWebsiteToDelete(site);
  };

  const handleReindexClick = (site: IndexedWebsite, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate('/workspace/index', { state: { prefillUrl: site.source_url } });
  };

  return (
    <>
      <div className="mt-6 flex flex-col gap-2">
        <div className="flex items-center justify-between px-4 group">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Knowledge Bases
          </span>
          <button
            onClick={() => navigate('/workspace/index')}
            className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-opacity p-1"
            title="Add website"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-col gap-1 px-2">
          {state.websites.length === 0 ? (
            <div className="px-3 py-2 text-sm text-slate-500 italic">No websites indexed yet.</div>
          ) : (
            state.websites.map((site) => (
              <div
                key={site.website_id}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-200 dark:hover:bg-white/5 transition-colors cursor-pointer group relative ${
                  state.selectedWebsiteId === site.website_id ? 'bg-slate-200 dark:bg-white/5' : ''
                }`}
                onClick={() => {
                  setSelectedWebsiteId(site.website_id);
                }}
              >
                <Database className={`w-4 h-4 transition-colors ${state.selectedWebsiteId === site.website_id ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400'}`} />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate flex-1 min-w-0">
                  {site.domain || site.source_url}
                </span>
                
                {isDeleting === site.website_id ? (
                  <Loader2 className="w-3 h-3 text-rose-500 dark:text-rose-400 animate-spin" />
                ) : (
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="flex items-center justify-center w-4">
                      {site.status === 'indexed' && (
                        <div className="w-2 h-2 rounded-full bg-emerald-500" title="Indexed" />
                      )}
                      {site.status === 'processing' && (
                        <Loader2 className="w-3 h-3 text-amber-500 animate-spin" title="Processing" />
                      )}
                      {site.status === 'failed' && (
                        <AlertCircle className="w-3 h-3 text-rose-500" title="Failed" />
                      )}
                    </div>
                    <button
                      className="opacity-0 group-hover:opacity-100 flex items-center justify-center p-1.5 text-slate-400 dark:text-slate-500 hover:text-blue-500 dark:hover:text-blue-400 hover:bg-blue-500/10 transition-all rounded-md"
                      onClick={(e) => handleReindexClick(site, e)}
                      title="Re-index website"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="opacity-0 group-hover:opacity-100 flex items-center justify-center p-1.5 text-slate-400 dark:text-slate-500 hover:text-rose-500 dark:hover:text-rose-400 hover:bg-rose-500/10 transition-all rounded-md"
                      onClick={(e) => handleDeleteClick(site, e)}
                      title="Delete website"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {websiteToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 max-w-sm w-full shadow-2xl animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">Delete Knowledge Base</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              Are you sure you want to delete <span className="font-semibold text-slate-900 dark:text-white">{websiteToDelete.domain || websiteToDelete.source_url}</span>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
                onClick={cancelDelete}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-rose-600 hover:bg-rose-500 transition-colors shadow-lg shadow-rose-900/20"
                onClick={confirmDelete}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
