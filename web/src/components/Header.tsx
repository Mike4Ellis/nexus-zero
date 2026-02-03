"use client";

import { useState, useEffect } from "react";

export function Header() {
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-[#2a2a2a] bg-[#0a0a0a]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-10 h-10 border-2 border-[#00ff88] flex items-center justify-center">
              <span className="text-[#00ff88] font-display font-bold text-lg">N</span>
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00ff88] animate-pulse" />
          </div>
          
          <div>
            <h1 className="font-display font-bold text-xl tracking-tight">
              NEXUS <span className="text-[#00ff88]">ZERO</span>
            </h1>
            <p className="text-xs text-[#555555] tracking-widest">
              INTELLIGENCE AGGREGATION
            </p>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a href="#" className="text-sm text-[#888888] hover:text-[#00ff88] transition-colors">
            DASHBOARD
          </a>
          <a href="#" className="text-sm text-[#888888] hover:text-[#00ff88] transition-colors">
            BRIEFS
          </a>
          <a href="#" className="text-sm text-[#888888] hover:text-[#00ff88] transition-colors">
            SOURCES
          </a>
          <a href="#" className="text-sm text-[#888888] hover:text-[#00ff88] transition-colors">
            ANALYTICS
          </a>
        </nav>
        
        {/* Time & Status */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-lg font-mono text-[#00ff88]">{currentTime}</div>
            <div className="text-xs text-[#555555]">UTC+8</div>
          </div>
          
          <div className="flex items-center gap-2 px-3 py-1 border border-[#2a2a2a] bg-[#141414]">
            <span className="status-dot status-active" />
            <span className="text-xs text-[#00ff88]">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
