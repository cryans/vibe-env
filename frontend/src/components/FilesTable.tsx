import React from 'react';
import type { UseMutationResult } from '@tanstack/react-query';

interface FileInfo {
  filename: string;
  status: 'staged' | 'persisted';
}

interface FileEvent {
  timestamp: string;
  eventType: string;
  payload: any;
}

interface FilesTableProps {
  files: FileInfo[] | undefined;
  isLoading: boolean;
  status: 'staged' | 'persisted';
  commitMutation?: UseMutationResult<void, any, string, any>;
  discardMutation?: UseMutationResult<void, any, string, any>;
  expandedFile: string | null;
  onToggleExpand: (filename: string) => void;
  fileEvents: FileEvent[] | undefined;
  isLoadingEvents: boolean;
}

const FilesTable: React.FC<FilesTableProps> = ({
  files,
  isLoading,
  status,
  commitMutation,
  discardMutation,
  expandedFile,
  onToggleExpand,
  fileEvents,
  isLoadingEvents,
}) => {
  if (isLoading) {
    return <p className="text-gray-500">Loading {status} files...</p>;
  }
  if (!files || files.length === 0) {
    return <p className="text-gray-500">No {status} files found.</p>;
  }

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/4">
              Actions
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              File ID / Filename
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {files.map((file) => {
            const isExpanded = expandedFile === file.filename;
            return (
              <React.Fragment key={file.filename}>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      {file.status === 'staged' ? (
                        <>
                          <button className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs font-medium transition-colors">
                            Tag
                          </button>
                          <button className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 text-xs font-medium transition-colors">
                            Transform
                          </button>
                          {commitMutation && (
                            <button
                              onClick={() => commitMutation.mutate(file.filename)}
                              disabled={commitMutation.isPending}
                              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-xs font-medium transition-colors disabled:bg-gray-400"
                            >
                              {commitMutation.isPending && commitMutation.variables === file.filename
                                ? 'Committing...'
                                : 'Commit'}
                            </button>
                          )}
                          {discardMutation && (
                            <button
                              onClick={() => discardMutation.mutate(file.filename)}
                              disabled={discardMutation.isPending}
                              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs font-medium transition-colors disabled:bg-gray-400"
                            >
                              {discardMutation.isPending && discardMutation.variables === file.filename
                                ? 'Discarding...'
                                : 'Discard'}
                            </button>
                          )}
                        </>
                      ) : (
                        <a
                          href={`/api/files/download/${file.filename}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 bg-indigo-500 text-white rounded hover:bg-indigo-600 text-xs font-medium transition-colors inline-block text-center"
                        >
                          Download
                        </a>
                      )}
                      <button
                        onClick={() => onToggleExpand(file.filename)}
                        className="px-3 py-1 bg-gray-100 text-blue-600 border border-gray-200 rounded hover:bg-gray-200 text-xs font-medium transition-colors"
                      >
                        {isExpanded ? 'Hide Lineage' : 'Show Lineage'}
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 break-all max-w-xs truncate">
                    {file.filename}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {file.status === 'staged' ? (
                      <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                        Staged
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        Persisted
                      </span>
                    )}
                  </td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td colSpan={3} className="px-6 py-4 bg-gray-50">
                      <div className="border-t border-gray-200 pt-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Lineage (Events)</h4>
                        {isLoadingEvents && <p className="text-sm text-gray-500">Loading events...</p>}
                        {!isLoadingEvents && (!fileEvents || fileEvents.length === 0) && (
                          <p className="text-sm text-gray-500">No events found for this file.</p>
                        )}
                        {!isLoadingEvents && fileEvents && fileEvents.length > 0 && (
                          <ul className="space-y-3 max-w-4xl">
                            {fileEvents.map((event, index) => (
                              <li key={index} className="bg-white p-3 rounded-md border border-gray-200 shadow-sm">
                                <p className="font-medium text-sm text-gray-800">
                                  Event: <span className="text-blue-600">{event.eventType}</span>
                                  <span className="text-gray-400 text-xs ml-2">
                                    ({new Date(event.timestamp).toLocaleString()})
                                  </span>
                                </p>
                                <details className="mt-1 text-xs">
                                  <summary className="cursor-pointer text-blue-500 hover:text-blue-700 font-medium select-none">
                                    View Payload
                                  </summary>
                                  <pre className="bg-gray-50 p-2 rounded border border-gray-100 mt-1 overflow-x-auto text-xs text-gray-700 font-mono">
                                    {JSON.stringify(event.payload, null, 2)}
                                  </pre>
                                </details>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default FilesTable;
