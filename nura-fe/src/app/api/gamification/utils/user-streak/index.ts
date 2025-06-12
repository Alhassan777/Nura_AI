import dayjs from "dayjs";
import { createClient } from "@/utils/supabase/server";
import { handleStaticBadgesForType } from "../../badges/utils";

/**
 * Bump or reset a user's streak based on today's activity.
 *
 * @param userId       the UUID of the user
 * @param activityDate a Dayjs or Date representing when they acted (usually today)
 */
export async function updateUserStreak(
  userId: string,
  activityDate: string // e.g. dayjs().format('YYYY-MM-DD')
) {
  console.log(`[Streak] Starting update for user ${userId} with activity date ${activityDate}`);
  const supabase = await createClient();
  // 1) Load the user's current streak state
  const { data: user, error: fetchErr } = await supabase
    .from("users")
    .select("current_streak, last_activity, freeze_credits")
    .eq("id", userId)
    .single();

  if (fetchErr || !user) {
    console.error(`[Streak] Error fetching user ${userId}:`, fetchErr || "User not found");
    throw fetchErr ?? new Error("User not found");
  }

  const { current_streak, last_activity, freeze_credits } = user;
  console.log(`[Streak] User data: streak=${current_streak}, lastActivity=${last_activity}, freezeCredits=${freeze_credits}`);

  const prevDate = last_activity ? dayjs(last_activity) : null;
  const today = dayjs(activityDate);
  const gapDays = prevDate ? today.diff(prevDate, "day") : Infinity;
  console.log(`[Streak] Gap days calculated: ${gapDays}`);

  // 2) If already did something today, do nothing
  if (prevDate && gapDays === 0) {
    console.log(`[Streak] Already active today, keeping streak at ${current_streak}`);
    return { newStreak: current_streak, remainingFreezes: freeze_credits };
  }


  // 3) Straight continuation if they acted yesterday
  if (gapDays === 1) {
    console.log(`[Streak] Continuous streak (yesterday activity), incrementing to ${current_streak + 1}`);
    const { error: updErr } = await supabase
      .from("users")
      .update({
        current_streak: current_streak + 1,
        last_activity: activityDate,
      })
      .eq("id", userId);

    if (updErr) {
      console.error(`[Streak] Error updating continuous streak:`, updErr);
      throw updErr;
    }


    return { newStreak: current_streak + 1, remainingFreezes: freeze_credits };
  }

  // 4) Gap within available freezes?
  //    e.g. gapDays=3 means they missed 2 days; need freeze_credits >= 2
  const neededFreezes = gapDays > 1 ? gapDays - 1 : 0;
  console.log(`[Streak] Needed freezes: ${neededFreezes}, available: ${freeze_credits}`);

  if (neededFreezes > 0 && neededFreezes <= freeze_credits) {
    // consume freezes and bump
    console.log(`[Streak] Using ${neededFreezes} freeze credits to maintain streak`);
    const { error: consErr } = await supabase
      .from("users")
      .update({
        freeze_credits: freeze_credits - neededFreezes,
        current_streak: current_streak + 1,
        last_activity: activityDate,
      })
      .eq("id", userId);

    if (consErr) {
      console.error(`[Streak] Error consuming freeze credits:`, consErr);
      throw consErr;
    }

    try {
      // (optional) log each freeze usage
      const freezeDate = today.subtract(1, "day").format("YYYY-MM-DD");
      console.log(`[Streak] Logging freeze usage for date: ${freezeDate}`);

      const { error: freezeLogErr } = await supabase.from("user_freeze_usages").insert({
        user_id: userId,
        frozen_date: freezeDate,
      });

      if (freezeLogErr) {
        console.warn(`[Streak] Warning: Failed to log freeze usage:`, freezeLogErr);
        // Non-critical error, continue without throwing
      }
    } catch (freezeLogException) {
      console.warn(`[Streak] Exception in freeze logging:`, freezeLogException);
      // Non-critical exception, continue without throwing
    }

    return {
      newStreak: current_streak + 1,
      remainingFreezes: freeze_credits - neededFreezes,
    };
  }

  // 5) Otherwise, streak is broken—archive the old streak, then reset to 1
  console.log(`[Streak] Streak broken. Archiving old streak of ${current_streak} days`);

  if (current_streak > 0 && prevDate) {
    try {
      const startDate = prevDate.subtract(current_streak - 1, "day").format("YYYY-MM-DD");
      console.log(`[Streak] Archiving streak from ${startDate} to ${prevDate.format("YYYY-MM-DD")}`);

      const { error: archiveErr } = await supabase.from("user_streaks").insert({
        user_id: userId,
        start_date: startDate,
        end_date: prevDate.format("YYYY-MM-DD"),
        length: current_streak,
      });

      if (archiveErr) {
        console.warn(`[Streak] Warning: Failed to archive streak:`, archiveErr);
        // Non-critical error, continue without throwing
      }
    } catch (archiveException) {
      console.warn(`[Streak] Exception in streak archiving:`, archiveException);
      // Non-critical exception, continue without throwing
    }
  }

  // reset
  console.log(`[Streak] Resetting streak to 1`);
  const { error: resetErr } = await supabase
    .from("users")
    .update({
      current_streak: 1,
      last_activity: activityDate,
    })
    .eq("id", userId);

  if (resetErr) {
    console.error(`[Streak] Error resetting streak:`, resetErr);
    throw resetErr;
  }

  console.log(`[Streak] Successfully reset streak for user ${userId}`);
  await handleStaticBadgesForType(userId, "streak");

  return { newStreak: 1, remainingFreezes: freeze_credits };
}
