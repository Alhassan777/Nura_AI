import { TagType } from "@/types/tag";
import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import dayjs from "dayjs";
import { awardXp } from "./award-xp";
import { updateUserStreak } from "./user-streak";
import { handleDailyReflectionQuest } from ".";
import { handleStaticBadgesForType } from "../badges/utils";

export async function addReflection(
  userId: string,
  {
    mood,
    note,
    tags,
  }: {
    mood: string;
    note: string;
    tags: TagType[];
  }
) {
  console.log("Adding reflection", { mood, note, tags, userId });
  const supabase = await createSupabaseClient();

  // 1) Save the reflection
  const { data: refl, error: reflError } = await supabase
    .from("reflections")
    .insert({
      user_id: userId,
      mood,
      note,
      tags,
    })
    .select("id")
    .single();

  if (reflError) {
    console.error("Error saving reflection:", reflError);
    throw reflError;
  }

  // 2) Award XP for this reflection
  const newXp = await awardXp(userId, 20, "reflection");

  // 3) Update streak
  await updateUserStreak(userId, dayjs().format("YYYY-MM-DD"));

  // 4) Handle daily reflection quest
  await handleDailyReflectionQuest(userId);

  // 5) Handle static badges
  await handleStaticBadgesForType(userId, "reflections");

  return { reflectionId: refl.id, xp: newXp };
}
