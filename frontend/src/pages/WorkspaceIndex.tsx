import React from 'react';
import { Navigate } from 'react-router-dom';
import { useWorkspaceStore } from '../hooks/useWorkspaceStore';
import { EmptyChatState } from '../components/EmptyChatState';

export const WorkspaceIndex: React.FC = () => {
  const { state } = useWorkspaceStore();

  if (state.conversations.length > 0) {
    // Navigate to the most recently updated conversation
    const sorted = [...state.conversations].sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
    return <Navigate to={`chat/${sorted[0].id}`} replace />;
  }

  return <EmptyChatState />;
};

export default WorkspaceIndex;
