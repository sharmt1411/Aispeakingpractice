import React from 'react';
import StarParticle from './StarParticle';

interface StarFieldProps {
  isActive: boolean;
}

const StarField: React.FC<StarFieldProps> = ({ isActive }) => {
  return (
    <div className="absolute -inset-32">
      {Array.from({ length: 48 }).map((_, i) => (
        <StarParticle key={i} index={i} isActive={isActive} />
      ))}
    </div>
  );
};

export default StarField;