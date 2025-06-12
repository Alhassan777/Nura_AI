export * from './award-xp';
export * from './user-streak';

import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import dayjs from "dayjs";
import { awardXp } from "./award-xp";

export async function handleDailyReflectionQuest(userId: string) {
  const supabase = await createSupabaseClient();

  // 1) Count how many reflections the user created today
  const todayStart = dayjs().startOf("day").toISOString();
  const todayEnd = dayjs().endOf("day").toISOString();

  const { data: reflections, error: reflectionsError } = await supabase
    .from("reflections")
    .select("id")
    .eq("user_id", userId)
    .gte("created_at", todayStart)
    .lt("created_at", todayEnd);

  if (reflectionsError) {
    console.error("Error counting today's reflections:", reflectionsError);
    throw reflectionsError;
  }

  const reflectionsCount = reflections?.length ?? 0;

  // 2) Fetch the system quest with key "reflections"
  const { data: quest, error: questError } = await supabase
    .from("quests")
    .select("id, frequency, xp_reward")
    .eq("type", "system")
    .eq("key", "reflections")
    .single();

  if (questError) {
    console.error("Error fetching reflections quest:", questError);
    throw questError;
  }
  if (!quest) return;

  // 3) If the user has met or exceeded the required count, attempt to insert into user_quests
  if (reflectionsCount >= quest.frequency) {
    const { id: questId } = quest;

    // Check if it's already marked completed today
    const { data: existing, error: existingError } = await supabase
      .from("user_quests")
      .select("id")
      .eq("user_id", userId)
      .eq("quest_id", questId)
      .gte("completed_at", todayStart)
      .lt("completed_at", todayEnd)
      .limit(1);

    if (existingError) {
      console.error("Error checking existing user_quests:", existingError);
      throw existingError;
    }

    if (!existing || existing.length === 0) {
      const { error: insertError } = await supabase.from("user_quests").insert({
        user_id: userId,
        quest_id: questId,
      });

      if (insertError) {
        console.error("Error inserting into user_quests:", insertError);
        throw insertError;
      }

      await awardXp(userId, quest.xp_reward, "quest");
      return;
    }
  }
}
