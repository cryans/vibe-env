import React from 'react';
import { Sparkles } from 'lucide-react';
import { useAppStore } from '../store/appStore';

const Header: React.FC = () => {
  const { configuredModel, toggleSidebar } = useAppStore();

  return (
    <header className="flex items-center justify-between p-4 bg-white border-b shadow-sm">
      <div className="flex items-center gap-2">
        <button onClick={toggleSidebar} className="p-1 mr-2 rounded hover:bg-gray-100">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <Sparkles className="w-6 h-6 text-blue-500" />
        <h1 className="text-xl font-medium text-gray-800">Gemini Clone</h1>
      </div>
      <div className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
        Model: {configuredModel}
      </div>
    </header>
  );
};

export default Header;
