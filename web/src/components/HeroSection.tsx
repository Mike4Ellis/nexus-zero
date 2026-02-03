"use client";

import { useEffect, useState } from "react";

export function HeroSection() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className={`space-y-6 ${mounted ? "animate-slide-up" : "opacity-0"}`}>
      {/* Main headline */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs text-[#555555] tracking-widest">
          <span className="w-8 h-px bg-[#00ff88]" />
          <span>SYSTEM STATUS</span>
        </div>
        
        <h2 className="font-display text-4xl md:text-6xl font-bold leading-tight">
          INFORMATION
          <br />
          <span className="text-[#00ff88]">NEXUS</span> ACTIVE
        </h2>
        
        <p className="text-[#888888] max-w-xl text-sm md:text-base">
          Automated aggregation and curation from X, Reddit, RSS feeds.
          Dual-score filtering for maximum signal, minimum noise.
        </p>
      </div>
      
      {/* Quick stats bar */}
      <div className="flex flex-wrap gap-4 md:gap-8 pt-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 border border-[#2a2a2a] flex items-center justify-center">
            <span className="text-2xl font-display font-bold text-[#ff3366]">42</span>
          </div>
          <div>
            <div className="text-xs text-[#555555]">TODAY</div>
            <div className="text-sm">ITEMS</div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 border border-[#2a2a2a] flex items-center justify-center">
            <span className="text-2xl font-display font-bold text-[#00ccff]">3</span>
          </div>
          <div>
            <div className="text-xs text-[#555555]">ACTIVE</div>
            <div className="text-sm">SOURCES</div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 border border-[#2a2a2a] flex items-center justify-center">
            <span className="text-2xl font-display font-bold text-[#00ff88]">79%</span>
          </div>
          <div>
            <div className="text-xs text-[#555555]">PROJECT</div>
            <div className="text-sm">COMPLETE</div>
          </div>
        </div>
      </div>
    </section>
  );
}
