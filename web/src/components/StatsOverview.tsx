"use client";

import { useEffect, useState } from "react";

interface Stats {
  totalContents: number;
  todayContents: number;
  pendingBriefs: number;
  activeSources: number;
}

export function StatsOverview() {
  const [stats, setStats] = useState<Stats>({
    totalContents: 0,
    todayContents: 0,
    pendingBriefs: 0,
    activeSources: 0,
  });

  useEffect(() => {
    // TODO: Fetch from API
    setStats({
      totalContents: 1234,
      todayContents: 56,
      pendingBriefs: 2,
      activeSources: 4,
    });
  }, []);

  const statItems = [
    { label: "总收录内容", value: stats.totalContents, color: "bg-blue-500" },
    { label: "今日新增", value: stats.todayContents, color: "bg-green-500" },
    { label: "待生成简报", value: stats.pendingBriefs, color: "bg-yellow-500" },
    { label: "活跃数据源", value: stats.activeSources, color: "bg-purple-500" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <div key={item.label} className="bg-white rounded-lg shadow p-6">
          <div className={`w-12 h-12 ${item.color} rounded-lg mb-4`} />
          <p className="text-sm text-gray-600">{item.label}</p>
          <p className="text-2xl font-bold text-gray-900">{item.value}</p>
        </div>
      ))}
    </div>
  );
}
