"use client";

import { useEffect, useState } from "react";

interface StatCardProps {
  label: string;
  value: string;
  subtext: string;
  color: "accent" | "heat" | "potential" | "info";
  delay?: number;
}

function StatCard({ label, value, subtext, color, delay = 0 }: StatCardProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const colorClasses = {
    accent: "border-[#00ff88] text-[#00ff88]",
    heat: "border-[#ff3366] text-[#ff3366]",
    potential: "border-[#00ccff] text-[#00ccff]",
    info: "border-[#ffaa00] text-[#ffaa00]",
  };

  return (
    <div
      className={`
        border ${colorClasses[color]} bg-[#141414] p-6
        transition-all duration-500
        ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
        hover:bg-[#1a1a1a] hover:shadow-lg hover:shadow-${color === "accent" ? "[#00ff8833]" : color === "heat" ? "[#ff336633]" : color === "potential" ? "[#00ccff33]" : "[#ffaa0033]"}
      `}
    >
      <div className="text-xs text-[#555555] tracking-widest mb-2">{label}</div>
      <div className="font-display text-3xl font-bold mb-1">{value}</div>
      <div className="text-xs text-[#888888]">{subtext}</div>
    </div>
  );
}

export function StatsGrid() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-[#555555] tracking-widest">
        <span className="w-8 h-px bg-[#00ff88]" />
        <span>METRICS</span>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="TOTAL"
          value="11/14"
          subtext="US COMPLETED"
          color="accent"
          delay={0}
        />
        <StatCard
          label="HEAT"
          value="10"
          subtext="TRENDING ITEMS"
          color="heat"
          delay={100}
        />
        <StatCard
          label="POTENTIAL"
          value="5"
          subtext="HIDDEN GEMS"
          color="potential"
          delay={200}
        />
        <StatCard
          label="SCHEDULER"
          value="4"
          subtext="ACTIVE JOBS"
          color="info"
          delay={300}
        />
      </div>
    </div>
  );
}
