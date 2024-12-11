import React from 'react';

interface StarParticleProps {
  index: number;
  isActive: boolean;
}

const StarParticle: React.FC<StarParticleProps> = ({ index, isActive }) => {
  const angle = (index * Math.PI * 2) / 24;
  const distance = 200 + Math.random() * 100;
  const startX = Math.cos(angle) * distance;
  const startY = Math.sin(angle) * distance;
  const size = 5 + Math.random() * 3;
  const delay = Math.random() * 2;
  // const delay = (index / 24) * 2;
  
  return (
    <div
      className={`absolute left-1/2 top-1/2 rounded-full
        ${isActive ? 'animate-star-attract' : 'opacity-0'}
        transition-opacity duration-300`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        '--start-x': `${startX}px`,
        '--start-y': `${startY}px`,
        animationDelay: `${delay}s`,
        background: `radial-gradient(circle at center,
          rgba(255, ${180 + index * 5}, ${200 + index * 5}, ${isActive ? 0.9 : 0})
          rgba(255, ${150 + index * 5}, ${170 + index * 5}, 0))`,
        boxShadow: `0 0 ${size * 2}px rgba(255, ${180 + index * 5}, ${200 + index * 5}, ${isActive ? 0.5 : 0})`,
      } as React.CSSProperties}
    />
  );
};

export default StarParticle;