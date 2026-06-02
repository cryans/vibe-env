import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAppStore } from '../store/appStore';
import FilesTable from './FilesTable';

interface FileInfo {
  filename: string;
  status: 'staged' | 'persisted';
}

interface FileEvent {
  timestamp: string;
  eventType: string;
  payload: any; // JSON payload
}

const fetchStagedFiles = async (): Promise<FileInfo[]> => {
  const { data } = await axios.get<string[]>('/api/files/staged');
  return data.map(filename => ({ filename, status: 'staged' }));
};

const fetchPersistedFiles = async (): Promise<FileInfo[]> => {
  const { data } = await axios.get<string[]>('/api/files/persisted');
  return data.map(filename => ({ filename, status: 'persisted' }));
};

const fetchFileEvents = async (filename: string): Promise<FileEvent[]> => {
  const { data } = await axios.get<FileEvent[]>(`/api/files/events/${filename}`);
  return data;
};

const commitFile = async (filename: string): Promise<void> => {
  await axios.post(`/api/files/${filename}/commit`);
};

const discardFile = async (filename: string): Promise<void> => {
  await axios.post(`/api/files/${filename}/discard`);
};

const FileViewer: React.FC = () => {
  const queryClient = useQueryClient();
  const setAlertMessage = useAppStore((state) => state.setAlertMessage);
  const { data: stagedFiles, isLoading: isLoadingStaged } = useQuery<FileInfo[]>({ queryKey: ['stagedFiles'], queryFn: fetchStagedFiles });
  const { data: persistedFiles, isLoading: isLoadingPersisted } = useQuery<FileInfo[]>({ queryKey: ['persistedFiles'], queryFn: fetchPersistedFiles });

  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  const { data: fileEvents, isLoading: isLoadingEvents } = useQuery<FileEvent[]>(
    { queryKey: ['fileEvents', expandedFile], queryFn: () => fetchFileEvents(expandedFile!), enabled: !!expandedFile }
  );

  const commitMutation = useMutation({
    mutationFn: commitFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stagedFiles'] });
      queryClient.invalidateQueries({ queryKey: ['persistedFiles'] });
    },
    onError: (err: any) => {
      console.error(err);
      const errMsg = err.response?.data?.detail || err.message || 'Failed to commit file.';
      setAlertMessage(errMsg);
    },
  });

  const discardMutation = useMutation({
    mutationFn: discardFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stagedFiles'] });
      queryClient.invalidateQueries({ queryKey: ['persistedFiles'] });
    },
    onError: (err: any) => {
      console.error(err);
      const errMsg = err.response?.data?.detail || err.message || 'Failed to discard file.';
      setAlertMessage(errMsg);
    },
  });

  const toggleExpand = (filename: string) => {
    setExpandedFile(expandedFile === filename ? null : filename);
  };

  return (
    <div className="p-4 space-y-8">
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-4">Staged Files</h3>
        <FilesTable
          files={stagedFiles}
          isLoading={isLoadingStaged}
          status="staged"
          commitMutation={commitMutation}
          discardMutation={discardMutation}
          expandedFile={expandedFile}
          onToggleExpand={toggleExpand}
          fileEvents={fileEvents}
          isLoadingEvents={isLoadingEvents}
        />
      </div>

      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-4">Persisted Files</h3>
        <FilesTable
          files={persistedFiles}
          isLoading={isLoadingPersisted}
          status="persisted"
          expandedFile={expandedFile}
          onToggleExpand={toggleExpand}
          fileEvents={fileEvents}
          isLoadingEvents={isLoadingEvents}
        />
      </div>
    </div>
  );
};

export default FileViewer;
