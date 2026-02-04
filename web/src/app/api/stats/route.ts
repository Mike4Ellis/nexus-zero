import { NextResponse } from "next/server";

interface Stats {
  totalContents: number;
  todayContents: number;
  pendingBriefs: number;
  activeSources: number;
}

// Mock data - replace with actual database query
const mockStats: Stats = {
  totalContents: 1234,
  todayContents: 56,
  pendingBriefs: 2,
  activeSources: 4,
};

export async function GET() {
  try {
    // TODO: Connect to actual database
    // const stats = await db.query(`
    //   SELECT 
    //     (SELECT COUNT(*) FROM contents) as total_contents,
    //     (SELECT COUNT(*) FROM contents WHERE DATE(created_at) = CURRENT_DATE) as today_contents,
    //     (SELECT COUNT(*) FROM daily_briefs WHERE telegram_sent = false) as pending_briefs,
    //     (SELECT COUNT(*) FROM sources WHERE is_active = true) as active_sources
    // `);
    
    return NextResponse.json({
      success: true,
      data: mockStats,
    });
  } catch (error) {
    console.error("Failed to fetch stats:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
