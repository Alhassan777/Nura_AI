// src/services/badges.ts
import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import dayjs from "dayjs";
import { awardXp } from "../utils/award-xp";

export type Badge = {
  id: number;
  name: string;
  description: string;
  threshold_type: string;
  threshold_value: number;
  icon: string;
  created_at: string;
};

export async function getBadgesGroupedByType(): Promise<
  Record<string, Badge[]>
> {
  const supabase = await createSupabaseClient();

  const { data: user, error: userError } = await supabase.auth.getUser();
  if (userError) {
    console.error("Error fetching user:", userError);
    throw userError;
  }
  const userId = user.user?.id;

  // 1) Fetch all badges, ordering by threshold so UI shows small→large
  const { data: badges, error } = await supabase
    .from("badges")
    .select("*")
    .order("threshold_value", { ascending: true });

  if (error) {
    console.error("Error fetching badges:", error);
    throw error;
  }

  const { data: userBadges, error: userBadgesError } = await supabase
    .from("user_badges")
    .select("*")
    .eq("user_id", userId);

  if (userBadgesError) {
    console.error("Error fetching user badges:", userBadgesError);
    throw userBadgesError;
  }

  // 2) Reduce into groups keyed by threshold_type
  return badges!.reduce((groups, badge) => {
    const key = badge.threshold_type;
    if (!groups[key]) groups[key] = [];
    badge.unlocked =
      userBadges?.some((ub) => ub.badge_id === badge.id) ?? false;
    groups[key].push(badge);
    return groups;
  }, {} as Record<string, Badge[]>);
}

/**
 * Awards all static badges of a given threshold_type for a user.
 *
 * @param userId         The ID of the user to check/award badges for.
 * @param thresholdType  One of: "reflections", "friends", "streak", etc.
 */
export async function handleStaticBadgesForType(
  userId: string,
  thresholdType: string
) {
  const supabase = await createSupabaseClient();

  // 1) Fetch all badges that match this thresholdType
  const { data: badges, error: badgesError } = await supabase
    .from("badges")
    .select("id, threshold_value, xp_award")
    .eq("threshold_type", thresholdType)
    .order("threshold_value", { ascending: true });

  if (badgesError) {
    console.error(
      `Error fetching badges for type "${thresholdType}":`,
      badgesError
    );
    throw badgesError;
  }
  if (!badges || badges.length === 0) {
    // Nothing to do if there are no badges of this type
    return;
  }

  // 2) Determine the user's current metric for this thresholdType
  let userMetric = 0;

  switch (thresholdType) {
    case "reflections": {
      // Count total reflections the user has ever created
      const { count: totalReflections, error: reflCountError } = await supabase
        .from("reflections")
        .select("id", { count: "exact", head: true })
        .eq("user_id", userId);

      if (reflCountError) {
        console.error("Error counting reflections:", reflCountError);
        throw reflCountError;
      }
      userMetric = totalReflections ?? 0;
      break;
    }

    case "friends": {
      // Count how many accepted friends this user has
      const { count: totalFriends, error: friendsCountError } = await supabase
        .from("friends")
        .select("id", { count: "exact", head: true })
        .eq("user_id", userId)
        .eq("status", "accepted");

      if (friendsCountError) {
        console.error("Error counting friends:", friendsCountError);
        throw friendsCountError;
      }
      userMetric = totalFriends ?? 0;
      break;
    }

    case "streak": {
      // Fetch the user's current streak from the user_streaks table
      const { data: streakRow, error: streakError } = await supabase
        .from("users")
        .select("current_streak")
        .eq("id", userId)
        .single();

      if (streakError && streakError.code !== "PGRST116") {
        console.error("Error fetching user streak:", streakError);
        throw streakError;
      }
      userMetric = streakRow?.current_streak ?? 0;
      break;
    }

    // Add more cases here if you have other threshold types
    default:
      console.warn(`Unhandled thresholdType "${thresholdType}".`);
      return;
  }

  // 3) For each badge whose threshold_value ≤ userMetric, award if not already
  for (const badge of badges) {
    const { id: badgeId, threshold_value } = badge;
    if (userMetric < threshold_value) {
      // Skip badges the user hasn't reached yet
      continue;
    }

    // Check if the user already has this badge
    const { data: existing, error: existingError } = await supabase
      .from("user_badges")
      .select("id")
      .eq("user_id", userId)
      .eq("badge_id", badgeId)
      .limit(1);

    if (existingError) {
      console.error("Error checking existing badge:", existingError);
      throw existingError;
    }

    // If not awarded, insert a new row
    if (!existing || existing.length === 0) {
      const { error: insertError } = await supabase.from("user_badges").insert({
        user_id: userId,
        badge_id: badgeId,
      });
      await awardXp(userId, badge.xp_award, "badge");
      if (insertError) {
        console.error("Error inserting user_badges:", insertError);
        throw insertError;
      }
    }
  }
}
