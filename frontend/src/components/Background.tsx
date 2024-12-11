import React from 'react';

const Background: React.FC = () => {
  return (
    <div className="fixed inset-0 w-full h-full bg-gradient animate-gradient">
      {/* <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 animate-gradient-shift"></div> */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-100 via-pink-100 to-pink-500 animate-gradient-shift"></div>
    </div>
  );
};

export default Background;