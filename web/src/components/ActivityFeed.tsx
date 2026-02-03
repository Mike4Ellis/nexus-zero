"use client";

import { useEffect, useState } from "react";

interface Activity {
  id: number;
  type: "fetch" | "score" | "brief" | "send";
  message: string;
  timestamp: string;
  status: "success" | "pending" | "error";
}

export function ActivityFeed() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Mock activities
  const activities: Activity[] = [
    { id: 1, type: "fetch", message: "Fetched 15 items from X", timestamp: "10:23", status: "success" },
    { id: 2, type: "score", message: "Calculated scores for 42 items", timestamp: "09:45", status: "success" },
    { id: 3, type: "brief", message: "Generated daily brief", timestamp: "08:00", status: "success" },
    { id: 4, type: "send", message: "Sent brief via Telegram", timestamp: "08:30", status: "success" },
    { id: 5, type: "fetch", message: "Fetched 12 items from Reddit", timestamp: "06:23", status: "success" },
  ];

  const getIcon = (type: Activity["type"]) => {
    switch (type) {
      case "fetch":
        return "↓";
      case "score":
        return "⚡";
      case "brief":
        return "📄";
      case "send":
        return "→";
      default:
        return "•";
    }
  };

  const getColor = (type: Activity["type"]) => {
    switch (type) {
      case "fetch":
        return "text-[#00ccff]";
      case "score":
        return "text-[#ffaa00]";
      case "brief":
        return "text-[#00ff88]";
      case "send":
        return "text-[#ff3366]";
      default:
        return "text-[#888888]";
    }
  };

  return (
    <div
      className={`
        border border-[#2a2a2a] bg-[#141414] h-full
        transition-all duration-500
        ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
      `}
    >
      {/* Header */}
      <div className="p-6 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2 text-xs text-[#555555] tracking-widest">
          <span className="w-8 h-px bg-[#00ff88]" />
          <span>ACTIVITY LOG</span>
        </div>
      </div>
      
      {/* Feed */}
      <div className="p-6">
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <div
              key={activity.id}
              className="flex gap-3 group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Icon */}
              <div className={`text-lg ${getColor(activity.type)}`}>
                {getIcon(activity.type)}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[#f5f5f5] group-hover:text-white transition-colors">
                  {activity.message}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#555555]">{activity.timestamp}</span>
                  {activity.status === "success" && (
                    <span className="text-xs text-[#00ff88]">✓</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Live indicator */}
        <div className="mt-6 pt-4 border-t border-[#2a2a2a]">
          <div className="flex items-center gap-2">
            <span className="status-dot status-active animate-pulse" />
            <span className="text-xs text-[#00ff88]">LIVE FEED</span>
          </div>
        </div>
      </div>
    </div>
  );
}
