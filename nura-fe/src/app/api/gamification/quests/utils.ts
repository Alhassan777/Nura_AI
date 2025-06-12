import { createClient } from "@/utils/supabase/server";
import { SupabaseClient } from "@supabase/supabase-js";

export type Quest = {
  id: string;
  key: string;
  frequency: number;
  title: string;
  description: string;
  xp_reward: number;
  type: "system" | "user";
  time_frame: "daily" | "weekly" | "monthly";
  progress: QuestProgress;
  created_at: string;
};

export type QuestProgress = {
  count?: number;
  completed?: boolean;
  status?: string;
  completedAt?: string | null;
};

//
// 1. Separate function to handle progress for a single system‐quest key
//
async function getQuestProgress(
  supabase: SupabaseClient,
  quest: Quest,
  userId: string
): Promise<QuestProgress> {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  switch (quest.key) {
    case "reflections": {
      // Count how many reflections the user created today
      const { count: totalReflections, error: countError } = await supabase
        .from("reflections")
        .select("id", { count: "exact", head: true })
        .eq("user_id", userId)
        .gte("created_at", today.toISOString())
        .lt("created_at", tomorrow.toISOString());
      if (countError) {
        throw new Error(countError.message);
      }

      const count = totalReflections ?? 0;
      const completed = count >= quest.frequency;

      // if (completed) {
      //   // Upsert a “completed today” row into user_quests
      //   const todayDateString = today.toISOString().slice(0, 10); // “YYYY-MM-DD”
      //   const { error: upsertError } = await supabase
      //     .from("user_quests")
      //     .upsert(
      //       {
      //         user_id: userId,
      //         quest_id: quest.id,
      //         quest_date: todayDateString,
      //         status: "COMPLETED",
      //         completed_at: new Date().toISOString(),
      //         started_at: new Date().toISOString(),
      //         updated_at: new Date().toISOString(),
      //       },
      //       { onConflict: ["user_id", "quest_id", "quest_date"] }
      //     );
      //   if (upsertError) {
      //     throw new Error(upsertError.message);
      //   }
      // }

      return { count, completed };
    }

    // If you add more system‐level keys (e.g. “friends”, “mood_tags”, etc.), handle them here:
    // case "friends": {
    //   // Example: count how many “friend” rows today, then upsert user_quests…
    //   break;
    // }

    default: {
      // For any other system quest, look up user_quests directly
      const { data: uq, error: uqError } = await supabase
        .from("user_quests")
        .select("status, completed_at")
        .eq("user_id", userId)
        .eq("quest_id", quest.id)
        .single();

      if (uqError && uqError.code !== "PGRST116") {
        // PGRST116 = no rows found; ignore that
        throw new Error(uqError.message);
      }

      if (!uq) {
        return { status: "NOT_STARTED" };
      }
      return { status: uq.status, completedAt: uq.completed_at };
    }
  }
}

//
// 2. Main function uses getQuestProgress() for each system quest
//
export const getUserQuests = async () => {
  const supabase = await createClient();
  const { data: user, error: userError } = await supabase.auth.getUser();
  if (userError || !user?.user) {
    throw new Error(userError?.message || "User not authenticated");
  }
  const userId = user.user.id;

  // Fetch all system-defined quests
  const { data: systemQuests, error: systemQuestsError } = await supabase
    .from("quests")
    .select("*")
    .eq("type", "system");
  if (systemQuestsError) {
    throw new Error(systemQuestsError.message);
  }

  const enhancedQuests: Quest[] = [];
  for (const quest of systemQuests ?? []) {
    const progress = await getQuestProgress(supabase, quest as Quest, userId);
    enhancedQuests.push({ ...quest, progress });
  }

  // Fetch custom (user) quests for this user
  const { data: userQuests, error: userQuestsError } = await supabase
    .from("quests")
    .select("*")
    .eq("type", "user")
    .eq("user_id", userId);
  if (userQuestsError) {
    throw new Error(userQuestsError.message);
  }

  return { systemQuests: enhancedQuests, userQuests };
};
