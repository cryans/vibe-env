import React, { RefObject } from 'react';
import { Bot } from 'lucide-react';
import ChatMessage from './ChatMessage';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  messagesEndRef: RefObject<HTMLDivElement>;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  messagesEndRef,
}) => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {messages.map((msg, idx) => (
        <ChatMessage key={idx} item={msg} idx={idx} />
      ))}

      {isLoading && (
        <div className="flex gap-4 justify-start">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-blue-600" />
          </div>
          <div className="px-4 py-3 rounded-2xl bg-white border shadow-sm text-gray-800 rounded-bl-none">
            <div className="flex gap-1 items-center h-6">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
