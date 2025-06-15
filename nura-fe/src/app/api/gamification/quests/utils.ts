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

export type CreateQuestType = Omit<
  Quest,
  "id" | "key" | "progress" | "created_at" | "type"
>;

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

  // Helper function to get time frame boundaries
  const getTimeFrameBoundaries = (timeFrame: string) => {
    const now = new Date();
    let startDate: Date;
    let endDate: Date;

    switch (timeFrame) {
      case "daily":
        startDate = new Date(now);
        startDate.setHours(0, 0, 0, 0);
        endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + 1);
        break;
      case "weekly":
        startDate = new Date(now);
        const dayOfWeek = startDate.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Monday = 0
        startDate.setDate(startDate.getDate() - daysToMonday);
        startDate.setHours(0, 0, 0, 0);
        endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + 7);
        break;
      case "monthly":
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        break;
      case "one_time":
      default:
        // For one_time quests, we don't use time boundaries
        return { startDate: null, endDate: null };
    }

    return { startDate, endDate };
  };

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
      const { startDate, endDate } = getTimeFrameBoundaries(quest.time_frame);

      // For one_time quests, check if ever completed
      if (quest.time_frame === "one_time") {
        const { data: uq, error: uqError } = await supabase
          .from("user_quests")
          .select("status, completed_at, count")
          .eq("user_id", userId)
          .eq("quest_id", quest.id)
          .single();

        if (uqError && uqError.code !== "PGRST116") {
          console.error(uqError.message);
          throw new Error(uqError.message);
        }

        if (!uq) {
          return { status: "NOT_STARTED", count: 0, completed: false };
        }

        return {
          status: uq.status,
          completedAt: uq.completed_at,
          count: uq.count || 0,
          completed: uq.status === "COMPLETED",
        };
      }

      // For time-based quests (daily, weekly, monthly)
      if (startDate && endDate) {
        // Check for progress within the current time frame
        const { data: uq, error: uqError } = await supabase
          .from("user_quests")
          .select("status, completed_at, count, created_at")
          .eq("user_id", userId)
          .eq("quest_id", quest.id)
          .gte("created_at", startDate.toISOString())
          .lt("created_at", endDate.toISOString())
          .order("created_at", { ascending: false })
          .limit(1);

        if (uqError) {
          throw new Error(uqError.message);
        }

        // If no progress in current time frame, reset to 0
        if (!uq || uq.length === 0) {
          return { status: "NOT_STARTED", count: 0, completed: false };
        }

        const latestProgress = uq[0];

        // Check if quest was completed in this time frame
        const isCompleted =
          latestProgress.status === "COMPLETED" &&
          latestProgress.completed_at &&
          new Date(latestProgress.completed_at) >= startDate &&
          new Date(latestProgress.completed_at) < endDate;

        return {
          status: latestProgress.status,
          completedAt: latestProgress.completed_at,
          count: latestProgress.count || 0,
          completed: isCompleted,
        };
      }

      // Fallback for any edge cases
      return { status: "NOT_STARTED", count: 0, completed: false };
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

  // Get the quest details to check XP reward, frequency, and time_frame
  const { data: quest, error: questError } = await supabase
    .from("quests")
    .select("xp_reward, type, frequency, time_frame")
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

  // Helper function to get time frame boundaries
  const getTimeFrameBoundaries = (timeFrame: string) => {
    const now = new Date();
    let startDate: Date;
    let endDate: Date;

    switch (timeFrame) {
      case "daily":
        startDate = new Date(now);
        startDate.setHours(0, 0, 0, 0);
        endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + 1);
        break;
      case "weekly":
        startDate = new Date(now);
        const dayOfWeek = startDate.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        startDate.setDate(startDate.getDate() - daysToMonday);
        startDate.setHours(0, 0, 0, 0);
        endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + 7);
        break;
      case "monthly":
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        break;
      case "one_time":
      default:
        return { startDate: null, endDate: null };
    }

    return { startDate, endDate };
  };

  const { startDate, endDate } = getTimeFrameBoundaries(quest.time_frame);

  let existingProgress;
  let existingError;

  if (quest.time_frame === "one_time") {
    // For one-time quests, check if ever completed
    const result = await supabase
      .from("user_quests")
      .select("id, count, status")
      .eq("user_id", userId)
      .eq("quest_id", questId)
      .single();

    existingProgress = result.data;
    existingError = result.error;
  } else if (startDate && endDate) {
    // For time-based quests, check progress within current time frame
    const result = await supabase
      .from("user_quests")
      .select("id, count, status, created_at")
      .eq("user_id", userId)
      .eq("quest_id", questId)
      .gte("created_at", startDate.toISOString())
      .lt("created_at", endDate.toISOString())
      .order("created_at", { ascending: false })
      .limit(1);

    existingProgress = result.data?.[0];
    existingError = result.error;
  }

  if (existingError && existingError.code !== "PGRST116") {
    throw new Error(existingError.message);
  }

  let newCount = 1;
  let newStatus = "IN_PROGRESS";

  if (existingProgress) {
    // Quest entry already exists, increment count
    newCount = (existingProgress.count || 0) + 1;

    if (existingProgress.status === "COMPLETED") {
      // For time-based quests, if already completed in this time frame, don't allow more progress
      if (quest.time_frame !== "one_time") {
        throw new Error(
          `Quest already completed for this ${quest.time_frame} period`
        );
      } else {
        throw new Error("Quest already completed");
      }
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
        completed_at:
          newStatus === "COMPLETED" ? new Date().toISOString() : null,
      })
      .eq("id", existingProgress.id);

    if (updateError) {
      throw new Error(updateError.message);
    }
  } else {
    // Create new entry
    const { error: insertError } = await supabase.from("user_quests").insert({
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
    total: quest.frequency,
    timeFrame: quest.time_frame,
  };
};
