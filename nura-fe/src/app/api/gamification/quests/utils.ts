import { createClient } from "@/utils/supabase/server";
import { SupabaseClient } from "@supabase/supabase-js";
import { awardXp } from "../utils/award-xp";

export type Quest = {
  id: string;
  key: string;
  frequency: number;
  title: string;
  description?: string;
  xp_reward: number;
  type: "system" | "user";
  time_frame: "daily" | "weekly" | "monthly" | "one_time";
  progress: QuestProgress;
  created_at: string;
};

export type CreateQuestType = Omit<Quest, "id" | "key" | "progress" | "created_at" | "type">;

export type QuestProgress = {
  count?: number;
  completed?: boolean;
  status?: string;
  completedAt?: string | null;
};

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


      return { count, completed };
    }


    default: {
      const { data: uq, error: uqError } = await supabase
        .from("user_quests")
        .select("status, completed_at, count")
        .eq("user_id", userId)
        .eq("quest_id", quest.id)
        .single();

      if (uqError && uqError.code !== "PGRST116") {
        throw new Error(uqError.message);
      }

      if (!uq) {
        return { status: "NOT_STARTED", count: 0, completed: false };
      }

      return {
        status: uq.status,
        completedAt: uq.completed_at,
        count: uq.count || 0,
        completed: uq.status === "COMPLETED"
      };
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

  const enhancedSystemQuests: Quest[] = [];
  for (const quest of systemQuests ?? []) {
    const progress = await getQuestProgress(supabase, quest as Quest, userId);
    enhancedSystemQuests.push({ ...quest, progress });
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

  const enhancedUserQuests: Quest[] = [];
  for (const quest of userQuests ?? []) {
    const progress = await getQuestProgress(supabase, quest as Quest, userId);
    enhancedUserQuests.push({ ...quest, progress });
  }

  return {
    systemQuests: enhancedSystemQuests,
    userQuests: enhancedUserQuests,
  };
};

export const createQuest = async (quest: CreateQuestType) => {
  const supabase = await createClient();
  const { data: user, error: userError } = await supabase.auth.getUser();
  if (userError || !user?.user) {
    throw new Error(userError?.message || "User not authenticated");
  }
  const { data, error } = await supabase.from("quests").insert({
    ...quest,
    user_id: user.user.id,
    type: "user",
  });
  if (error) {
    throw new Error(error.message);
  }
  return data;
};

export const completeQuest = async (questId: string) => {
  const supabase = await createClient();
  const { data: user, error: userError } = await supabase.auth.getUser();
  if (userError || !user?.user) {
    throw new Error(userError?.message || "User not authenticated");
  }
  const userId = user.user.id;

  // Get the quest details to check XP reward and frequency
  const { data: quest, error: questError } = await supabase
    .from("quests")
    .select("xp_reward, type, frequency")
    .eq("id", questId)
    .eq("type", "user")
    .eq("user_id", userId)
    .single();

  if (questError) {
    throw new Error(questError.message);
  }

  if (!quest) {
    throw new Error("Quest not found or not authorized");
  }

  // Check existing progress
  const { data: existingProgress, error: existingError } = await supabase
    .from("user_quests")
    .select("id, count, status")
    .eq("user_id", userId)
    .eq("quest_id", questId)
    .single();

  if (existingError && existingError.code !== "PGRST116") {
    throw new Error(existingError.message);
  }

  let newCount = 1;
  let newStatus = "IN_PROGRESS";

  if (existingProgress) {
    // Quest entry already exists, increment count
    newCount = (existingProgress.count || 0) + 1;

    if (existingProgress.status === "COMPLETED") {
      throw new Error("Quest already completed");
    }
  }

  // Check if quest will be completed with this action
  if (newCount >= quest.frequency) {
    newStatus = "COMPLETED";
  }

  if (existingProgress) {
    // Update existing entry
    const { error: updateError } = await supabase
      .from("user_quests")
      .update({
        count: newCount,
        status: newStatus,
        completed_at: newStatus === "COMPLETED" ? new Date().toISOString() : null,
      })
      .eq("user_id", userId)
      .eq("quest_id", questId);

    if (updateError) {
      throw new Error(updateError.message);
    }
  } else {
    // Create new entry
    const { error: insertError } = await supabase
      .from("user_quests")
      .insert({
        user_id: userId,
        quest_id: questId,
        status: newStatus,
        count: newCount,
        completed_at: newStatus === "COMPLETED" ? new Date().toISOString() : null,
      });

    if (insertError) {
      throw new Error(insertError.message);
    }
  }

  // Award XP only if quest is completed
  if (newStatus === "COMPLETED") {
    await awardXp(userId, quest.xp_reward, "quest");
  }

  return {
    success: true,
    completed: newStatus === "COMPLETED",
    progress: newCount,
    total: quest.frequency
  };
};