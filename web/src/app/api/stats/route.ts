import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stats`, {
      next: { revalidate: 30 }, // Revalidate every 30 seconds
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    
    // Fallback to mock data if backend is not available
    return NextResponse.json({
      totalContents: 1234,
      todayContents: 56,
      pendingBriefs: 2,
      activeSources: 4,
    });
  }
}
