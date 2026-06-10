import React from 'react';
import { MessageSquare, History, Settings } from 'lucide-react';
import { useAppStore } from '../store/appStore.ts';
import type { ViewMode, SessionInfo } from '../store/appStore.ts';

const Sidebar: React.FC = () => {
  const {
    isSidebarOpen,
    viewMode,
    directChatSessions,
    setViewMode,
    startNewDirectChat,
    loadDirectChatHistory,
    navigateToPiDevSessions,
    refreshModelsConfig,
  } = useAppStore();

  return (
    <div className={`w-64 bg-gray-100 border-r border-gray-200 flex flex-col ${isSidebarOpen ? '' : 'hidden'}`}>
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-700">Navigation</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('direct_chat')}
            className={`flex-1 flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${viewMode === 'direct_chat' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200 text-gray-700'}`}
          >
            <MessageSquare className="w-5 h-5" />
            <span>DirectChat</span>
          </button>
          <button
            onClick={startNewDirectChat}
            className="px-3 py-2 rounded-lg text-blue-600 hover:bg-blue-100 transition-colors font-medium border border-transparent hover:border-blue-200"
            title="New Direct Chat"
          >
            + New
          </button>
        </div>

        {directChatSessions.length > 0 && (
          <div className="mt-1 mb-4 space-y-0.5">
            {directChatSessions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => loadDirectChatHistory(s.filename)}
                className="w-full text-left truncate text-xs px-9 py-1.5 rounded text-gray-500 hover:bg-gray-200 hover:text-gray-900 transition-colors"
                title={s.title || s.id || s.filename}
              >
                {s.title || s.id || s.filename}
              </button>
            ))}
          </div>
        )}

        <button
          onClick={navigateToPiDevSessions}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${(viewMode === 'pidev_sessions' || viewMode === 'pidev_session_detail') ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200 text-gray-700'}`}
        >
          <History className="w-5 h-5" />
          <span>PiDev Sessions</span>
        </button>
        <button
          onClick={() => { setViewMode('models'); refreshModelsConfig(); }}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${viewMode === 'models' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200 text-gray-700'}`}
        >
          <Settings className="w-5 h-5" />
          <span>Models</span>
        </button>
        <button
          onClick={() => setViewMode('data_explorer')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${viewMode === 'data_explorer' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200 text-gray-700'}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M3 3h18v18H3zM3 9h18M9 3v18"/></svg>
          <span>Data Explorer</span>
        </button>
        <button
          onClick={() => setViewMode('s3_facade')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${viewMode === 's3_facade' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200 text-gray-700'}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          <span>S3 Facade</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
