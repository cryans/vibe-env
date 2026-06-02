import React from 'react';
import { Sparkles } from 'lucide-react';

const WelcomeMessage: React.FC = () => (
  <div className="flex flex-col items-center justify-center h-64 text-center mt-20">
    <Sparkles className="w-12 h-12 text-blue-400 mb-4" />
    <h2 className="text-2xl md:text-4xl font-medium text-gray-700 mb-2">Hello, how can I help?</h2>
    <p className="text-gray-500">I am powered by a Python backend using the llm library.</p>
  </div>
);

export default WelcomeMessage;
