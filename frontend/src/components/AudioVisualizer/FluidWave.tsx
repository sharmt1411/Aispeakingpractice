import React, { useEffect, useRef } from 'react';

interface FluidWaveProps {
  isActive: boolean;
  index: number;
}

const FluidWave: React.FC<FluidWaveProps> = ({ isActive, index }) => {
  const pathRef = useRef<SVGPathElement>(null);
  
  useEffect(() => {
    if (!pathRef.current || !isActive) return;
    
    const animate = () => {
      const path = pathRef.current;
      if (!path) return;
      
      const time = Date.now() / 1000;
      const points = Array.from({ length: 8 }, (_, i) => {
        const angle = (i / 8) * Math.PI * 2;
        const radius = 30 + Math.sin(time * 2 + i + index) * 5;
        const x = Math.cos(angle + time) * radius;
        const y = Math.sin(angle + time) * radius;
        return `${x},${y}`;
      });
      
      path.setAttribute('d', `M ${points[0]} C ${points.slice(1).join(' ')}`);
      requestAnimationFrame(animate);
    };
    
    const animation = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animation);
  }, [isActive, index]);

  return (
    <path
      ref={pathRef}
      fill="none"
      stroke={`rgba(255, ${100 + index * 30}, ${150 + index * 20}, ${isActive ? 0.6 : 0.2})`}
      strokeWidth="2"
      strokeLinecap="round"
      className="transform transition-opacity duration-300"
    />
  );
};

export default FluidWave;