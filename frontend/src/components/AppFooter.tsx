import React from 'react';
import { useAppStore } from '../store/appStore';
import { X } from 'lucide-react';

const AppFooter: React.FC = () => {
  const { alertMessage, setAlertMessage } = useAppStore();

  if (!alertMessage) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 bg-gray-800 text-white text-center text-sm z-50 flex items-center justify-center gap-4">
      <span>{alertMessage}</span>
      <button
        onClick={() => setAlertMessage(null)}
        className="p-1 rounded-full hover:bg-gray-700 transition-colors"
        aria-label="Dismiss alert"
      >
        <X size={16} />
      </button>
    </div>
  );
};

export default AppFooter;
