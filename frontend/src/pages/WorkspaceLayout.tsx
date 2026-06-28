import React from 'react';
import { Outlet } from 'react-router-dom';
import { AppSidebar } from '../components/AppSidebar';

export const WorkspaceLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-900 dark:bg-[#030712] dark:text-slate-100">
      <AppSidebar />
      <main className="flex-1 min-w-0 h-full overflow-hidden relative flex flex-col">
        <Outlet />
      </main>
    </div>
  );
};
