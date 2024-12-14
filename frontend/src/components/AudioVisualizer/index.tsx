import React, { useEffect, useRef, useState } from 'react';
import StarField from './StarField';

interface AudioVisualizerProps {
  isActive: boolean;
  Amplitude: Uint8Array
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ 
  isActive, 
  Amplitude
}) => {
  const siriWaveContainerRef = useRef<HTMLDivElement | null>(null);
  const siriWaveInstanceRef = useRef<any>(null);

  const updateAmplitude = (data: Uint8Array) => {
    if (!isActive || !siriWaveContainerRef.current) return;
    
    const newData = data.slice(0, 20);
    const int16Array = new Int16Array(newData.buffer, newData.byteOffset, newData.byteLength / 2);
    // console.log(">>>>>>>>>>int16Array", int16Array);
    const average = int16Array.reduce((sum, val) => sum + Math.abs(val), 0) / (10 * 32765);
    // console.log(">>>>>>>>>>average", average);
    

    const newAmplitude = Math.min(
      Math.max(
        average*5, 
        0.1  
      ), 
      1.0  
    );
    // console.log(">>>>>>>>>>newAmplitude", newAmplitude);
    if (siriWaveInstanceRef.current) {
      siriWaveInstanceRef.current.setAmplitude(newAmplitude);
    }
  };

  useEffect(() => {
    if (!isActive || !siriWaveContainerRef.current) return;
    if (Amplitude.length === 0) return;
    updateAmplitude(Amplitude);
  }, [Amplitude]);


  useEffect(() => {
    if (!isActive || !siriWaveContainerRef.current) return;

    if (siriWaveInstanceRef.current) {
      siriWaveInstanceRef.current.stop();
      siriWaveContainerRef.current.innerHTML = '';
    }

    const siriWave = new SiriWave({
      container: siriWaveContainerRef.current,
      width: siriWaveContainerRef.current.clientWidth || 800,
      height: siriWaveContainerRef.current.clientHeight || 200,
      color: '#ffffff', 
      amplitude: 0.1,    
      speed: 0.05,        
      frequency: 5,       
      style: 'ios'
    });

    siriWave.start();
    siriWaveInstanceRef.current = siriWave;

    return () => {
      if (siriWaveInstanceRef.current) {
        siriWaveInstanceRef.current.stop();
      }
      if (siriWaveContainerRef.current) {
        siriWaveContainerRef.current.innerHTML = ''; 
      }
    };
  }, [isActive, ]);


  return (
    <div className="absolute -inset-16 pointer-events-none overflow-hidden">
      <div className="relative w-full h-full">
        <div 
          ref={siriWaveContainerRef} 
          className="absolute bottom-5 left-0 right-0 h-32 opacity-50" 
        />
      </div>
    </div>
  );
};

export default AudioVisualizer;
