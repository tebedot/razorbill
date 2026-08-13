import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import VoiceMode from './components/VoiceMode';
import ChatDashboard from './components/ChatDashboard';

export type AppMode = 'voice' | 'chat' | 'memory' | 'settings';

function App() {
  const [currentMode, setCurrentMode] = useState<AppMode>('voice');

  return (
    <div className="app-container">
      <Sidebar currentMode={currentMode} onModeChange={setCurrentMode} />
      
      <main className="main-content">
        {currentMode === 'voice' && <VoiceMode />}
        {currentMode === 'chat' && <ChatDashboard />}
        {/* Memory and Settings are placeholders for now */}
        {currentMode === 'memory' && <div className="glass-panel" style={{margin: '24px', padding: '24px', height: 'calc(100% - 48px)'}}><h2>Memory Vault</h2><p className="text-muted">Long-term storage viewing interface coming soon.</p></div>}
        {currentMode === 'settings' && <div className="glass-panel" style={{margin: '24px', padding: '24px', height: 'calc(100% - 48px)'}}><h2>System Settings</h2><p className="text-muted">Configuration interface coming soon.</p></div>}
      </main>
    </div>
  );
}

export default App;
