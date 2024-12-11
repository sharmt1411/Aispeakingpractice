import React from 'react';
import StarField from './StarField';

interface AudioVisualizerProps {
  isActive: boolean;
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ isActive }) => {
  return (
    <div className="absolute -inset-16 pointer-events-none overflow-hidden">
      <div className="relative w-full h-full">
        <StarField isActive={isActive} />
      </div>
    </div>
  );
};

export default AudioVisualizer;