import React, { useCallback, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAppStore } from '../store/appStore';

const DragDropUploader: React.FC = () => {
  const [highlight, setHighlight] = useState(false);
  const { setAlertMessage } = useAppStore();

  const queryClient = useQueryClient();
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post('/api/files/stage', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setAlertMessage(`File uploaded successfully: ${data.filename}`);
      // Invalidate queries to refresh file list if any
      queryClient.invalidateQueries({ queryKey: ['stagedFiles'] });
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setAlertMessage('File upload failed!');
    },
  });

  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(false);

    const files = Array.from(e.dataTransfer.files);
    if (files && files.length > 0) {
      uploadMutation.mutate(files[0]); // Only uploading the first file for now
    }
  }, [uploadMutation]);
  const commonProps = {
    onDragEnter: handleDragEnter,
    onDragLeave: handleDragLeave,
    onDragOver: handleDragOver,
    onDrop: handleDrop,
  };

  return (
    <div
      {...commonProps}
      style={{
        border: `2px dashed ${highlight ? 'purple' : '#ccc'}`,
        borderRadius: '8px',
        padding: '20px',
        textAlign: 'center',
        cursor: 'pointer',
        minHeight: '150px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '20px 0',
      }}
    >
      {highlight ? (
        <p>Drop files here</p>
      ) : (
        <p>Drag 'n' drop some files here, or click to select files (not implemented yet)</p>
      )}
    </div>
  );
};

export default DragDropUploader;
