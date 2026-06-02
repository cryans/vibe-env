import React from 'react';
import { Bot, User, Wrench } from 'lucide-react';
import type { Message, SessionDetailItem } from '../store/appStore';

// This component is designed to render both simple chat messages and
// the more complex session detail items (which can include tool calls/results).
const ChatMessage: React.FC<{ item: Message | SessionDetailItem; idx: number }> = ({ item, idx }) => {
  // Handle custom llm logging format first (from PiDevSessionDetail)
  if ('prompt' in item && 'response' in item) {
    return (
      <div key={idx} className="mb-8">
        <div className="flex gap-4 justify-end mb-4">
          <div className="px-4 py-3 rounded-2xl max-w-[85%] bg-blue-600 text-white rounded-br-none">
            <p className="whitespace-pre-wrap leading-relaxed">{item.prompt}</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
            <User className="w-5 h-5 text-gray-600" />
          </div>
        </div>
        <div className="flex gap-4 justify-start">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-1">
            <Bot className="w-5 h-5 text-blue-600" />
          </div>
          <div className="px-4 py-3 rounded-2xl max-w-[85%] bg-white border shadow-sm text-gray-800 rounded-bl-none">
            <p className="whitespace-pre-wrap leading-relaxed">{item.response}</p>
          </div>
        </div>
      </div>
    );
  }

  // Handle standard Message interface (from DirectChat)
  const message = item as Message; // Cast for simpler type checking

  if (message.role === 'user' || message.role === 'assistant') {
    const isUser = message.role === 'user';
    return (
      <div key={idx} className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
        {!isUser && (
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-1">
            <Bot className="w-5 h-5 text-blue-600" />
          </div>
        )}
        <div className={`px-4 py-3 rounded-2xl max-w-[85%] ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-white border shadow-sm text-gray-800 rounded-bl-none'
        }`}>
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>
        {isUser && (
          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
            <User className="w-5 h-5 text-gray-600" />
          </div>
        )}
      </div>
    );
  }

  // Handle the more complex 'message' structure from SessionDetailItem (PiDev Sessions)
  const sessionMsg = (item as SessionDetailItem).message;
  if (!sessionMsg) return null;

  const isUser = sessionMsg.role === 'user';
  const isToolResult = sessionMsg.role === 'toolResult';
  const contents = Array.isArray(sessionMsg.content) ? sessionMsg.content : [{ type: 'text', text: sessionMsg.content }];

  if (isToolResult) {
    return (
      <div key={idx} className="flex gap-4 justify-start mb-6">
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 mt-1">
          <Wrench className="w-5 h-5 text-gray-500" />
        </div>
        <div className="px-4 py-3 rounded-2xl max-w-[85%] bg-gray-50 border shadow-sm text-gray-800 rounded-bl-none">
          <div className="text-xs font-semibold text-gray-500 mb-1">Tool Result: {sessionMsg.toolName}</div>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {contents.map((c: any, i: number) => {
            if (c.type === 'text' && c.text) {
              return <pre key={i} className="whitespace-pre-wrap overflow-x-auto text-xs">{c.text}</pre>;
            }
            return null;
          })}
        </div>
      </div>
    );
  }

  return (
    <div key={idx} className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-1">
          <Bot className="w-5 h-5 text-blue-600" />
        </div>
      )}
      <div className={`px-4 py-3 rounded-2xl max-w-[85%] ${
        isUser
          ? 'bg-blue-600 text-white rounded-br-none'
          : 'bg-white border shadow-sm text-gray-800 rounded-bl-none'
      }`}>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {contents.map((c: any, i: number) => {
          if (c.type === 'text' && c.text) {
            return <p key={i} className="whitespace-pre-wrap leading-relaxed">{c.text}</p>;
          }
          if (c.type === 'toolCall') {
            return (
              <div key={i} className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-sm text-gray-600 font-mono">
                <div className="flex items-center gap-1 font-semibold mb-1 text-gray-700">
                  <Wrench className="w-4 h-4" /> Tool Call: {c.name}
                </div>
                <pre className="whitespace-pre-wrap overflow-x-auto text-xs">{JSON.stringify(c.arguments, null, 2)}</pre>
              </div>
            );
          }
          return null;
        })}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
