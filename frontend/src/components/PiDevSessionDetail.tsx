import React from 'react';
import ChatMessage from './ChatMessage';
import { useAppStore } from '../store/appStore';
import type { SessionDetailItem } from '../store/appStore';

const PiDevSessionDetail: React.FC = () => {
  const { activePiDevSessionDetail, clearPiDevSessionDetail } = useAppStore();

  if (!activePiDevSessionDetail) {
    return (
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          <p>No session detail loaded.</p>
          <button onClick={clearPiDevSessionDetail} className="mt-4 text-blue-600 hover:underline flex items-center gap-1">
            &larr; Back to PiDev Sessions
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <button onClick={clearPiDevSessionDetail} className="mb-6 text-blue-600 hover:underline flex items-center gap-1">
          &larr; Back to PiDev Sessions
        </button>
        <div className="space-y-2">
          {activePiDevSessionDetail.map((item, idx) => (
            <ChatMessage key={idx} item={item} idx={idx} />
          ))}
        </div>
      </div>
    </main>
  );
};

export default PiDevSessionDetail;
