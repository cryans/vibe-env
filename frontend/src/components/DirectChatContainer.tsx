import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import MessageList from './MessageList';
import DirectChatInput from './DirectChatInput';
import WelcomeMessage from './WelcomeMessage';
import { useAppStore } from '../store/appStore';
import type { Message, SessionInfo } from '../store/appStore';

interface DirectChatContainerProps {
  isSidebarOpen: boolean; // Still passed for layout purposes, e.g., footer margin
}

const DirectChatContainer: React.FC<DirectChatContainerProps> = ({
  isSidebarOpen,
}) => {
  const {
    currentDirectChatMessages,
    currentDirectChatSessionId,
    addDirectChatMessage,
    addDirectChatSessionToList,
  } = useAppStore();

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when messages or loading state changes
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentDirectChatMessages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    // Add user message to local state first for immediate display
    addDirectChatMessage('user', userMsg);
    setIsLoading(true);

    try {
      const isCommand = userMsg.startsWith('!');
      const endpoint = isCommand ? '/api/command' : '/api/chat';
      const payload = isCommand ? { command: userMsg } : { message: userMsg, session_id: currentDirectChatSessionId };

      const response = await axios.post(endpoint, payload);
      addDirectChatMessage('assistant', response.data.response);

      // After a successful exchange, if it's a new session, notify parent to add it to sidebar
      // We check if it's the first message from the user in this session
      const allMessages = useAppStore.getState().currentDirectChatMessages; // Get latest state
      const userMessagesCount = allMessages.filter(m => m.role === 'user').length;
      if (userMessagesCount === 1 && allMessages.length === 2) { // First user msg + first assistant response
        const newSessionInfo: SessionInfo = {
          id: currentDirectChatSessionId,
          timestamp: new Date().toISOString(),
          filename: `chat_${currentDirectChatSessionId}.jsonl`, // Placeholder, backend might return actual
          source: 'chat',
          title: userMsg.substring(0, 30) || 'New Chat',
        };
        addDirectChatSessionToList(newSessionInfo);
      }

    } catch (error) {
      console.error(error);
      addDirectChatMessage('assistant', 'Sorry, I encountered an error communicating with the backend.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-32">
      {currentDirectChatMessages.length === 0 && !isLoading ? (
        <WelcomeMessage />
      ) : (
        <MessageList messages={currentDirectChatMessages} isLoading={isLoading} messagesEndRef={messagesEndRef} />
      )}
      <DirectChatInput
        input={input}
        onInputChange={(e) => setInput(e.target.value)}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        isSidebarOpen={isSidebarOpen}
      />
    </main>
  );
};

export default DirectChatContainer;
