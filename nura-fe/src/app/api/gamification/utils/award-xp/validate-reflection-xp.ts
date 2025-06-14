import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import dayjs from "dayjs";
import { getReflectionXpReward } from "@/utils/level-system";

export async function validateReflectionXp(userId: string): Promise<number> {
  const supabase = await createSupabaseClient();
  const todayStart = dayjs().startOf('day').toISOString();

  // Get user's current streak
  const { data: user, error: userError } = await supabase
    .from('users')
    .select('current_streak')
    .eq('id', userId)
    .single();

  if (userError) {
    console.error('validateReflectionXp > fetch user error:', userError);
    return 0;
  }

  // fetch all reflection xp_events from today
  const { data: events, error } = await supabase
    .from('xp_events')
    .select('amount, created_at')
    .eq('user_id', userId)
    .eq('event_type', 'reflection')
    .gte('created_at', todayStart)
    .order('created_at', { ascending: true });

  if (error) {
    console.error('validateReflectionXp > fetch events error:', error);
    return 0;
  }

  // filter only those that granted >0 XP
  const usedSlots = events.filter(e => e.amount > 0);
  const slotCount = usedSlots.length;

  // our 3‐slot schedule with streak bonus
  const baseXp = getReflectionXpReward(user?.current_streak || 0);
  const xpSchedule = [
    baseXp,                    // First reflection of the day
    Math.floor(baseXp * 0.5),  // Second reflection (50% of base)
    Math.floor(baseXp * 0.25)  // Third reflection (25% of base)
  ];

  // if still have a slot, award next slot
  if (slotCount < xpSchedule.length) {
    return xpSchedule[slotCount];
  }

  // otherwise no XP
  return 0;
}