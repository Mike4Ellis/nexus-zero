"use client";

import { useState, useEffect } from "react";

interface Brief {
  id: number;
  title: string;
  date: string;
  totalContents: number;
  platforms: Record<string, number>;
  heatTopCount: number;
  potentialCount: number;
}

export function BriefCard() {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch from API
    // For now, use mock data
    setBrief({
      id: 1,
      title: "Nexus Zero 每日简报 - 2026-02-03",
      date: "2026-02-03",
      totalContents: 42,
      platforms: { x: 15, reddit: 12, rss: 15 },
      heatTopCount: 10,
      potentialCount: 5,
    });
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
        暂无简报数据
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{brief.title}</h3>
          <span className="text-sm text-gray-500">{brief.date}</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">{brief.totalContents}</div>
            <div className="text-sm text-gray-600">收录内容</div>
          </div>
          
          <div className="bg-red-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-600">{brief.heatTopCount}</div>
            <div className="text-sm text-gray-600">热门精选</div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">{brief.potentialCount}</div>
            <div className="text-sm text-gray-600">潜力发现</div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-600">
              {Object.keys(brief.platforms).length}
            </div>
            <div className="text-sm text-gray-600">来源平台</div>
          </div>
        </div>
        
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">平台分布</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(brief.platforms).map(([platform, count]) => (
              <span
                key={platform}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800"
              >
                {platform}: {count}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
        <span className="text-sm text-gray-500">由 Nexus Zero 自动生成</span>
        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          查看详情 →
        </button>
      </div>
    </div>
  );
}
