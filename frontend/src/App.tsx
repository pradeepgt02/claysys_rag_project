import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { WorkspaceLayout } from './pages/WorkspaceLayout';
import { AddWebsitePage } from './pages/AddWebsitePage';
import { ChatPage } from './pages/ChatPage';

export const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/workspace" element={<WorkspaceLayout />}>
        {/* Default workspace route redirects to new chat or add index */}
        <Route index element={<Navigate to="chat/new" replace />} />
        <Route path="index" element={<AddWebsitePage />} />
        <Route path="chat/:chatId" element={<ChatPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
