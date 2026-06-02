import React from 'react';
import { useAppStore } from '../store/appStore';
import type { SessionInfo } from '../store/appStore';

const PiDevSessionsOverview: React.FC = () => {
  const { piDevSessions, loadPiDevSessionDetail } = useAppStore();

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-semibold mb-6">PiDev Sessions</h2>
        <div className="space-y-4">
          {piDevSessions.map((s, idx) => (
            <div key={idx} onClick={() => loadPiDevSessionDetail(s.filename)} className="p-4 bg-white border rounded-xl shadow-sm hover:shadow-md cursor-pointer transition-shadow">
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm text-gray-500">{s.id || s.filename}</span>
                <span className="text-sm text-gray-400">{new Date(s.timestamp).toLocaleString()}</span>
              </div>
              <div className="text-sm text-gray-600 font-medium">{s.cwd ? `Workspace: ${s.cwd}` : `Model: ${s.model_id || 'Custom'}`}</div>
            </div>
          ))}
          {piDevSessions.length === 0 && <p className="text-gray-500">No PiDev sessions found.</p>}
        </div>
      </div>
    </main>
  );
};

export default PiDevSessionsOverview;
