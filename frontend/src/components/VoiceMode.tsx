import React, { useState, useEffect } from 'react';
import Strands from './Strands';

type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

const VoiceMode: React.FC = () => {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.state) {
          setVoiceState(data.state);
        }
      } catch (e) {
        console.error("Invalid WS message", e);
      }
    };
    
    ws.onclose = () => {
      console.log("WebSocket connection closed. Ensure backend is running.");
      setVoiceState('idle');
    };

    return () => ws.close();
  }, []);

  const isSpeaking = voiceState === 'speaking';
  
  // When listening/idle/processing: All white strands
  // When speaking: 3 white strands, 1 vivid yellow strand (#ffe302)
  const strandColors = isSpeaking 
    ? ["#ffffff", "#ffffff", "#ffffff", "#ffe302"] 
    : ["#ffffff", "#ffffff", "#ffffff", "#ffffff"];

  // Status text map
  const statusMessages: Record<VoiceState, string> = {
    idle: 'Waiting... (Say "Hey Billy" to wake)',
    listening: 'Listening... (Speak now)',
    processing: 'Razor Bill is processing...',
    speaking: 'Razor Bill is speaking...'
  };

  return (
    <div className="voice-mode-container" style={{ width: '100%', height: '100%', position: 'relative', background: '#000000' }}>
      <Strands
        colors={strandColors}
        count={4}
        speed={0.5}
        amplitude={1}
        waviness={1}
        thickness={0.7}
        glow={2.6}
        taper={3}
        spread={1}
        intensity={0.6}
        saturation={1.5}
        opacity={1}
        scale={3} // Full screen scale
        glass={false}
        refraction={1}
        dispersion={1}
        glassSize={1}
      />
      
      <div className="status-text" style={{ position: 'absolute', bottom: '10%', zIndex: 10, color: '#ffffff' }}>
        <span className="status-indicator" style={{ backgroundColor: isSpeaking ? '#ffe302' : '#ffffff', boxShadow: `0 0 10px ${isSpeaking ? '#ffe302' : '#ffffff'}` }}></span>
        {statusMessages[voiceState]}
      </div>
    </div>
  );
};

export default VoiceMode;
