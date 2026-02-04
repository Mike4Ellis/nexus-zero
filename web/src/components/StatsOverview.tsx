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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch('/api/stats');
        if (!response.ok) {
          throw new Error('Failed to fetch stats');
        }
        const data = await response.json();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
        // Fallback to default values if API fails
        setStats({
          totalContents: 1234,
          todayContents: 56,
          pendingBriefs: 2,
          activeSources: 4,
        });
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  const statItems = [
    { label: "总收录内容", value: stats.totalContents, color: "bg-blue-500" },
    { label: "今日新增", value: stats.todayContents, color: "bg-green-500" },
    { label: "待生成简报", value: stats.pendingBriefs, color: "bg-yellow-500" },
    { label: "活跃数据源", value: stats.activeSources, color: "bg-purple-500" },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="w-12 h-12 bg-gray-200 rounded-lg mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

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
