import { NextResponse } from "next/server";
import { createClient } from "@/utils/supabase/server";
import dayjs from "dayjs";

export async function GET() {
  try {
    const supabase = await createClient();
    const { data: { user }, error: userError } = await supabase.auth.getUser();

    if (userError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = user.id;

    // Get user's current streak
    const { data: userData, error: userError2 } = await supabase
      .from("users")
      .select("current_streak")
      .eq("id", userId)
      .single();

    if (userError2) {
      console.error("Error fetching user streak:", userError2);
      return NextResponse.json({ error: "Error fetching user streak" }, { status: 500 });
    }

    // Get last 7 days of activity
    const sevenDaysAgo = dayjs().subtract(7, "day").startOf("day").toISOString();
    const { data: weekActivity, error: weekError } = await supabase
      .from("reflections")
      .select("created_at")
      .eq("user_id", userId)
      .gte("created_at", sevenDaysAgo)
      .order("created_at", { ascending: true });

    if (weekError) {
      console.error("Error fetching week activity:", weekError);
      return NextResponse.json({ error: "Error fetching week activity" }, { status: 500 });
    }

    // Get last 30 days of activity
    const thirtyDaysAgo = dayjs().subtract(30, "day").startOf("day").toISOString();
    const { data: monthActivity, error: monthError } = await supabase
      .from("reflections")
      .select("created_at")
      .eq("user_id", userId)
      .gte("created_at", thirtyDaysAgo)
      .order("created_at", { ascending: true });

    if (monthError) {
      console.error("Error fetching month activity:", monthError);
      return NextResponse.json({ error: "Error fetching month activity" }, { status: 500 });
    }

    // Calculate statistics
    const currentStreak = userData?.current_streak || 0;

    // Calculate 7-day progress
    const weekProgress = weekActivity ? Math.min(100, (weekActivity.length / 7) * 100) : 0;

    // Calculate 30-day progress
    const monthProgress = monthActivity ? Math.min(100, (monthActivity.length / 30) * 100) : 0;

    return NextResponse.json({
      currentStreak,
      weekProgress,
      monthProgress,
    });
  } catch (error) {
    console.error("Error in streak stats:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
} 