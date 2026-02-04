"""API client with caching and error handling."""

import useSWR from 'swr';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Fetcher function for SWR
async function fetcher<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

// Hooks for data fetching with caching
export function useStats() {
  return useSWR(
    `${API_BASE_URL}/api/stats`,
    fetcher<{
      totalContents: number;
      todayContents: number;
      pendingBriefs: number;
      activeSources: number;
    }>,
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: false,
    }
  );
}

export function useLatestBrief() {
  return useSWR(
    `${API_BASE_URL}/api/briefs/latest`,
    fetcher<{
      id: number;
      title: string;
      date: string;
      totalContents: number;
      platforms: Record<string, number>;
      heatTopCount: number;
      potentialCount: number;
    }>,
    {
      refreshInterval: 60000, // Refresh every minute
      revalidateOnFocus: false,
    }
  );
}

export function useContents(limit: number = 100) {
  return useSWR(
    `${API_BASE_URL}/api/contents?limit=${limit}`,
    fetcher<Array<{
      id: number;
      title: string;
      platform: string;
      published_at: string;
      heat_score: number;
      potential_score: number;
    }>>,
    {
      refreshInterval: 60000,
      revalidateOnFocus: false,
    }
  );
}
