import React, { useState, useEffect } from 'react';
import { ArrowUp, Database, Zap } from 'lucide-react';

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const ChatDashboard: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: 'assistant', content: 'Good day, Sir. How may I be of assistance today?' }
  ]);
  
  // Later we'll fetch from SQLite backend
  
  const handleSend = () => {
    if (!input.trim()) return;
    
    // Optimistic update
    const newMsg: Message = { id: Date.now(), role: 'user', content: input };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    
    // Mock response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: 'I have recorded your request in the logs, Sir. Shall I proceed with further analysis?' 
      }]);
    }, 1000);
  };

  return (
    <div className="chat-dashboard">
      <div className="chat-area">
        <div className="glass-panel chat-history">
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
        </div>
        
        <div className="chat-input-container">
          <input 
            type="text" 
            className="chat-input" 
            placeholder="Type your message to Razor Bill..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="send-btn" onClick={handleSend}>
            <ArrowUp size={24} />
          </button>
        </div>
      </div>
      
      <div className="memory-panel">
        <div className="panel-title">
          <Database size={20} /> 
          Active Session
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>CURRENT CONTEXT</p>
          <div style={{ background: 'rgb(30, 31, 32)', padding: '12px', borderRadius: '0', fontSize: '0.9rem' }}>
            Session ID: #124<br/>
            Memory Load: 4/10<br/>
            Model: Kimi K3 (Low Effort)
          </div>
        </div>
        
        <div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>ACTIVITY</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
            <Zap size={16} /> Backend Audio Engine Active
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatDashboard;
