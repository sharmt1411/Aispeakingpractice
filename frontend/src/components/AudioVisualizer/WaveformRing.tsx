import React from 'react';

interface WaveformRingProps {
  isActive: boolean;
  radius: number;
  barCount: number;
  baseRotation?: number;
}

const WaveformRing: React.FC<WaveformRingProps> = ({ 
  isActive, 
  radius, 
  barCount, 
  baseRotation = 0 
}) => {
  return (
    <div 
      className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
      style={{
        width: radius * 2,
        height: radius * 2,
        transform: `translate(-50%, -50%) rotate(${baseRotation}deg)`
      }}
    >
      {Array.from({ length: barCount }).map((_, i) => {
        const rotation = (i * (360 / barCount));
        const delay = (i / barCount) * 2;
        
        return (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 origin-bottom"
            style={{
              transform: `rotate(${rotation}deg)`,
              width: '2px',
              height: '8px',
              marginTop: -radius,
              backgroundColor: isActive ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.2)',
              animation: isActive ? `waveformPulse 2s ease-in-out infinite ${delay}s` : 'none',
            }}
          />
        );
      })}
    </div>
  );
};

export default WaveformRing;