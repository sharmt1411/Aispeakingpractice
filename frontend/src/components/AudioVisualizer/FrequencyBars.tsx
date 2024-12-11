import React from 'react';

interface FrequencyBarsProps {
  isActive: boolean;
}

const FrequencyBars: React.FC<FrequencyBarsProps> = ({ isActive }) => {
  const barCount = 32;
  const radius = 50;

  return (
    <div className="absolute inset-0">
      {Array.from({ length: barCount }).map((_, i) => {
        const angle = (i * 360) / barCount;
        const delay = (i / barCount) * 1.5;
        
        return (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 origin-bottom"
            style={{
              transform: `rotate(${angle}deg) translateY(-${radius}px)`,
              width: '2px',
              height: isActive ? '12px' : '4px',
              backgroundColor: `rgba(255, ${isActive ? '100' : '200'}, ${isActive ? '100' : '200'}, ${isActive ? 0.9 : 0.3})`,
              animation: isActive ? `frequencyBounce 1.5s ease-in-out infinite ${delay}s` : 'none',
              transition: 'all 0.3s ease-in-out',
            }}
          />
        );
      })}
    </div>
  );
};

export default FrequencyBars;