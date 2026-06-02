import React, { useEffect } from 'react';
import './App.css'; // Keep App.css for global styles
import { useAppStore } from './store/appStore';

import Header from './components/Header';
import Sidebar from './components/Sidebar';
import DirectChatContainer from './components/DirectChatContainer';
import PiDevSessionsOverview from './components/PiDevSessionsOverview';
import PiDevSessionDetail from './components/PiDevSessionDetail';
import ModelsView from './components/ModelsView';

function App() {
  const {
    viewMode,
    isSidebarOpen,
    configuredModel,
    activePiDevSessionDetail,
    piDevSessions,
    modelsList,
    loadInitialAppData,
  } = useAppStore();

  useEffect(() => {
    loadInitialAppData();
  }, [loadInitialAppData]);

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans">
      <Sidebar />
      
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header />

        {viewMode === 'direct_chat' && (
          <DirectChatContainer isSidebarOpen={isSidebarOpen} />
        )}

        {viewMode === 'pidev_sessions' && (
          <PiDevSessionsOverview />
        )}

        {viewMode === 'pidev_session_detail' && activePiDevSessionDetail && (
          <PiDevSessionDetail />
        )}

        {viewMode === 'models' && (
          <ModelsView modelsList={modelsList} />
        )}
      </div>
    </div>
  );
}

export default App;
