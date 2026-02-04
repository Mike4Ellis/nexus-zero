import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/briefs/latest`, {
      next: { revalidate: 60 }, // Revalidate every 60 seconds
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch brief:', error);
    
    // Fallback to mock data if backend is not available
    return NextResponse.json({
      id: 1,
      title: "Nexus Zero 每日简报 - 2026-02-04",
      date: "2026-02-04",
      totalContents: 42,
      platforms: { x: 15, reddit: 12, rss: 15 },
      heatTopCount: 10,
      potentialCount: 5,
    });
  }
}
