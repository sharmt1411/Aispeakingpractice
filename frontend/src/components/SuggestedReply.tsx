import React from 'react';

interface SuggestedReplyProps {
  message: string;
  // onSelect: (message: string) => void;
}

const SuggestedReply: React.FC<SuggestedReplyProps> = ({ message }) => {
  return (
    <button
      // onClick={() => onSelect(message)}
      className="w-full text-middle px-4 py-2.5 rounded-lg bg-white/5 
        hover:bg-white/10 transition-all duration-200 text-white/90 text-xs
        border border-white/10 hover:border-white/20 transform hover:scale-[1.02]"
    >
      {message}
    </button>
  );
};

export default SuggestedReply;