import React, { useState } from 'react';
import { Mic, MessageSquare, BrainCircuit, Settings, Menu } from 'lucide-react';
import type { AppMode } from '../App';

interface SidebarProps {
  currentMode: AppMode;
  onModeChange: (mode: AppMode) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentMode, onModeChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems: { id: AppMode; label: string; icon: React.ReactNode }[] = [
    { id: 'voice', label: 'Voice Assistant', icon: <Mic size={20} /> },
    { id: 'chat', label: 'Dashboard', icon: <MessageSquare size={20} /> },
    { id: 'memory', label: 'Memory Vault', icon: <BrainCircuit size={20} /> },
    { id: 'settings', label: 'Settings', icon: <Settings size={20} /> },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="brand">
        <div className="brand-title">Razor Bill</div>
        <div className="brand-icon" onClick={() => setIsCollapsed(!isCollapsed)}>
          <Menu size={20} />
        </div>
      </div>
      
      <nav className="nav-menu">
        {navItems.map((item) => (
          <div 
            key={item.id}
            className={`nav-item ${currentMode === item.id ? 'active' : ''}`}
            onClick={() => onModeChange(item.id)}
            title={isCollapsed ? item.label : ''}
          >
            {item.icon}
            <span className="nav-label">{item.label}</span>
          </div>
        ))}
      </nav>
      
      <div className="sys-status">
        System Status: <span>Online</span>
      </div>
    </aside>
  );
};

export default Sidebar;
