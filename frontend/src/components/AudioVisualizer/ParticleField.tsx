import React from 'react';

interface ParticleFieldProps {
  isActive: boolean;
}

const ParticleField: React.FC<ParticleFieldProps> = ({ isActive }) => {
  return (
    <div className="absolute inset-0">
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          className="absolute left-1/2 top-1/2 w-1 h-1 rounded-full"
          style={{
            transform: `rotate(${i * 30}deg) translateY(-40px)`,
            background: `rgba(255, 255, 255, ${isActive ? 0.8 : 0.2})`,
            animation: isActive ? `particleFloat 3s ease-in-out infinite ${i * 0.25}s` : 'none',
          }}
        />
      ))}
    </div>
  );
};

export default ParticleField;