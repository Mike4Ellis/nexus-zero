"use client";

import { useEffect, useState, useCallback } from "react";

interface ContentItem {
  id: number;
  title: string;
  platform: string;
  score: number;
  type: "heat" | "potential";
}

export function BriefPanel() {
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"heat" | "potential">("heat");

  useEffect(() => {
    setMounted(true);
  }, []);

  // Keyboard navigation for tabs
  const handleKeyDown = useCallback((e: React.KeyboardEvent, tab: "heat" | "potential") => {
    if (e.key === "ArrowRight" && tab === "heat") {
      setActiveTab("potential");
    } else if (e.key === "ArrowLeft" && tab === "potential") {
      setActiveTab("heat");
    }
  }, []);

  // Mock data
  const heatItems: ContentItem[] = [
    { id: 1, title: "AI breakthrough in protein folding", platform: "X", score: 95, type: "heat" },
    { id: 2, title: "New React framework announced", platform: "Reddit", score: 88, type: "heat" },
    { id: 3, title: "Crypto market analysis Q1 2026", platform: "RSS", score: 82, type: "heat" },
  ];

  const potentialItems: ContentItem[] = [
    { id: 4, title: "Indie game dev shares workflow", platform: "X", score: 72, type: "potential" },
    { id: 5, title: "Small cap stock deep dive", platform: "Reddit", score: 68, type: "potential" },
  ];

  const items = activeTab === "heat" ? heatItems : potentialItems;

  return (
    <div
      className={`
        border border-[#2a2a2a] bg-[#141414]
        transition-all duration-500
        ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2 text-xs text-[#555555] tracking-widest">
          <span className="w-8 h-px bg-[#00ff88]" aria-hidden="true" />
          <span>TODAY&apos;S BRIEF</span>
        </div>
        
        {/* Tabs with accessibility */}
        <div 
          className="flex gap-2" 
          role="tablist" 
          aria-label="Brief type selection"
        >
          <button
            role="tab"
            aria-selected={activeTab === "heat"}
            aria-controls="heat-panel"
            id="heat-tab"
            tabIndex={activeTab === "heat" ? 0 : -1}
            onClick={() => setActiveTab("heat")}
            onKeyDown={(e) => handleKeyDown(e, "heat")}
            className={`
              px-4 py-2 text-xs tracking-widest transition-all
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ff3366] focus-visible:ring-offset-2 focus-visible:ring-offset-[#141414]
              ${activeTab === "heat"
                ? "bg-[#ff3366] text-white"
                : "bg-[#1a1a1a] text-[#888888] hover:text-white"
              }
            `}
          >
            HEAT
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "potential"}
            aria-controls="potential-panel"
            id="potential-tab"
            tabIndex={activeTab === "potential" ? 0 : -1}
            onClick={() => setActiveTab("potential")}
            onKeyDown={(e) => handleKeyDown(e, "potential")}
            className={`
              px-4 py-2 text-xs tracking-widest transition-all
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00ccff] focus-visible:ring-offset-2 focus-visible:ring-offset-[#141414]
              ${activeTab === "potential"
                ? "bg-[#00ccff] text-white"
                : "bg-[#1a1a1a] text-[#888888] hover:text-white"
              }
            `}
          >
            POTENTIAL
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div 
        id="heat-panel"
        role="tabpanel"
        aria-labelledby="heat-tab"
        hidden={activeTab !== "heat"}
        className="p-6"
      >
        <div className="space-y-4">
          {heatItems.map((item, index) => (
            <article
              key={item.id}
              className="flex items-center gap-4 p-4 bg-[#0a0a0a] border border-[#2a2a2a] hover:border-[#333333] transition-colors group"
            >
              {/* Rank */}
              <div className="font-display text-2xl font-bold text-[#333333] group-hover:text-[#555555] transition-colors" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium truncate">{item.title}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#555555]">{item.platform}</span>
                  <span className="text-xs text-[#333333]" aria-hidden="true">//</span>
                  <span className="text-xs text-[#ff3366]">
                    SCORE: {item.score}
                  </span>
                </div>
              </div>
              
              {/* Indicator */}
              <div className="w-2 h-2 bg-[#ff3366]" aria-hidden="true" />
            </article>
          ))}
        </div>
      </div>

      <div 
        id="potential-panel"
        role="tabpanel"
        aria-labelledby="potential-tab"
        hidden={activeTab !== "potential"}
        className="p-6"
      >
        <div className="space-y-4">
          {potentialItems.map((item, index) => (
            <article
              key={item.id}
              className="flex items-center gap-4 p-4 bg-[#0a0a0a] border border-[#2a2a2a] hover:border-[#333333] transition-colors group"
            >
              {/* Rank */}
              <div className="font-display text-2xl font-bold text-[#333333] group-hover:text-[#555555] transition-colors" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium truncate">{item.title}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#555555]">{item.platform}</span>
                  <span className="text-xs text-[#333333]" aria-hidden="true">//</span>
                  <span className="text-xs text-[#00ccff]">
                    SCORE: {item.score}
                  </span>
                </div>
              </div>
              
              {/* Indicator */}
              <div className="w-2 h-2 bg-[#00ccff]" aria-hidden="true" />
            </article>
          ))}
        </div>
      </div>
        
      {/* Footer */}
      <div className="p-6 pt-0">
        <div className="pt-4 border-t border-[#2a2a2a] flex justify-between items-center">
          <span className="text-xs text-[#555555]">
            Generated: {new Date().toLocaleDateString()}
          </span>
          <button 
            className="text-xs text-[#00ff88] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00ff88] focus-visible:ring-offset-2 focus-visible:ring-offset-[#141414] rounded px-2 py-1"
          >
            VIEW ALL →
          </button>
        </div>
      </div>
    </div>
  );
}
