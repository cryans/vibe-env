import React from 'react';
import { Send } from 'lucide-react';

interface DirectChatInputProps {
  input: string;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isSidebarOpen: boolean;
}

const DirectChatInput: React.FC<DirectChatInputProps> = ({
  input,
  onInputChange,
  onSubmit,
  isLoading,
  isSidebarOpen,
}) => (
  <footer className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-gray-50 via-gray-50 to-transparent pt-10 pb-6 px-4" style={{ marginLeft: isSidebarOpen ? '16rem' : '0' }}>
    <div className="max-w-3xl mx-auto">
      <form onSubmit={onSubmit} className="relative flex items-center">
        <input
          type="text"
          value={input}
          onChange={onInputChange}
          placeholder="Enter a prompt here"
          className="w-full bg-white border border-gray-300 shadow-sm rounded-full py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-3 p-2 rounded-full text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-gray-400"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
      <p className="text-center text-xs text-gray-400 mt-3">
        LLM interactions might be inaccurate.
      </p>
    </div>
  </footer>
);

export default DirectChatInput;
