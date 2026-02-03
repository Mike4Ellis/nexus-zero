"use client";

import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { StatsGrid } from "@/components/StatsGrid";
import { BriefPanel } from "@/components/BriefPanel";
import { ActivityFeed } from "@/components/ActivityFeed";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] text-[#f5f5f5] font-mono">
      {/* Background grid */}
      <div className="fixed inset-0 bg-grid opacity-20 pointer-events-none" />
      
      {/* Content */}
      <div className="relative z-10">
        <Header />
        
        <div className="max-w-7xl mx-auto px-6 py-12">
          <HeroSection />
          
          <div className="mt-12 grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left column - Stats */}
            <div className="lg:col-span-2 space-y-8">
              <StatsGrid />
              <BriefPanel />
            </div>
            
            {/* Right column - Activity */}
            <div className="lg:col-span-1">
              <ActivityFeed />
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="mt-20 border-t border-[#2a2a2a] py-8">
          <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
            <div className="text-sm text-[#555555]">
              NEXUS ZERO // v1.0.0
            </div>
            <div className="flex items-center gap-2">
              <span className="status-dot status-active animate-pulse" />
              <span className="text-sm text-[#00ff88]">SYSTEM ONLINE</span>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
