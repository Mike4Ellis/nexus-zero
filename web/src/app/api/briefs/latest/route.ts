import { NextResponse } from "next/server";

interface Brief {
  id: number;
  title: string;
  date: string;
  totalContents: number;
  platforms: Record<string, number>;
  heatTopCount: number;
  potentialCount: number;
}

// Mock data - replace with actual database query
const mockBrief: Brief = {
  id: 1,
  title: "Nexus Zero 每日简报",
  date: new Date().toISOString().split("T")[0],
  totalContents: 42,
  platforms: { x: 15, reddit: 12, rss: 15 },
  heatTopCount: 10,
  potentialCount: 5,
};

export async function GET() {
  try {
    // TODO: Connect to actual database
    // const brief = await db.query('SELECT * FROM daily_briefs ORDER BY brief_date DESC LIMIT 1');
    
    return NextResponse.json({
      success: true,
      data: mockBrief,
    });
  } catch (error) {
    console.error("Failed to fetch latest brief:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch brief" },
      { status: 500 }
    );
  }
}
