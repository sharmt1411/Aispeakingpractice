import React from 'react';
import Background from './components/Background';
import VoiceChat from './components/VoiceChat';

function App() {
  return (
    <div className="relative min-h-screen">
      <Background />
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <VoiceChat />
      </div>
    </div>
  );
}

export default App;