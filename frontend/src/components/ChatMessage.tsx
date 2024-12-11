import React from 'react';

interface ChatMessageProps {
  message: string;
  sender: 'user' | 'other';
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, sender }) => {
  return (
    <div 
      className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-4 
        animate-fade-in-up`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          sender === 'user'
            ? 'bg-blue-300/90 text-white rounded-br-none'
            : 'bg-white/90 text-gray-800 rounded-bl-none'
        } backdrop-blur-sm shadow-lg`}
      >
        <p className="text-sm leading-relaxed">{message}</p>
      </div>
    </div>
  );
};

export default ChatMessage;