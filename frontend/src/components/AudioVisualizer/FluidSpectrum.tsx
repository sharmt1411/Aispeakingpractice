import React from 'react';
import FluidWave from './FluidWave';

interface FluidSpectrumProps {
  isActive: boolean;
}

const FluidSpectrum: React.FC<FluidSpectrumProps> = ({ isActive }) => {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <svg
        className="w-full h-full"
        viewBox="-50 -50 100 100"
        style={{
          transform: `rotate(${isActive ? 360 : 0}deg)`,
          transition: 'transform 20s linear infinite',
        }}
      >
        <g className="animate-spin-slow">
          {Array.from({ length: 5 }).map((_, i) => (
            <FluidWave key={i} isActive={isActive} index={i} />
          ))}
        </g>
      </svg>
    </div>
  );
};

export default FluidSpectrum;