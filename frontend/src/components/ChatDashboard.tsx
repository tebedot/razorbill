import React, { useState, useEffect, useRef } from 'react';
import { ArrowUp, Database, Zap } from 'lucide-react';

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const ChatDashboard: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastUserMessageRef = useRef<HTMLDivElement>(null);
  const prevMessagesLength = useRef(0);
  const [initialLoad, setInitialLoad] = useState(true);

  useEffect(() => {
    if (messages.length === 0) return;

    if (initialLoad) {
      // Instant snap on mount
      if (lastUserMessageRef.current) {
        lastUserMessageRef.current.scrollIntoView({ behavior: "auto", block: "start" });
      } else {
        messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
      }
      setInitialLoad(false);
    } else if (messages.length > prevMessagesLength.current) {
      // Smooth scroll only when NEW messages appear
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    
    prevMessagesLength.current = messages.length;
  }, [messages, initialLoad]);

  const fetchMessages = async () => {
    try {
      const res = await fetch('http://localhost:8001/messages');
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
        setSessionId(data.session_id);
      }
    } catch (e) {
      console.error("Failed to fetch messages", e);
    }
  };

  useEffect(() => {
    fetchMessages();
    // Poll every 3 seconds to sync with voice inputs
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, []);
  
  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userText = input;
    setInput('');
    
    // Optimistic update
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: userText }]);
    
    try {
      const res = await fetch('http://localhost:8001/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText })
      });
      
      if (res.ok) {
        // We let the polling pick up the AI response to avoid conflicts
        fetchMessages();
      }
    } catch (e) {
      console.error("Failed to send message", e);
    }
  };

  const lastUserMsgIndex = messages.map(m => m.role).lastIndexOf('user');

  return (
    <div className="chat-dashboard">
      <div className="chat-area">
        <div className="glass-panel chat-history" style={{ overflowY: 'auto' }}>
          {messages.map((msg, idx) => (
            <div 
              key={msg.id} 
              className={`message ${msg.role}`}
              ref={idx === lastUserMsgIndex ? lastUserMessageRef : null}
            >
              {msg.content.replace(/\*\*/g, '')}
            </div>
          ))}
          <div ref={messagesEndRef} />
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
            Session ID: #{sessionId || '...'}<br/>
            Memory Load: {messages.length}<br/>
            Model: Kimi K3
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
