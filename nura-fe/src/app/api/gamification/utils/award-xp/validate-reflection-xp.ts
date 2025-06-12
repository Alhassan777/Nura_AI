import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import dayjs from "dayjs";

export async function validateReflectionXp(userId: string): Promise<number> {
  const supabase = await createSupabaseClient();
  const todayStart = dayjs().startOf('day').toISOString();

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

  // our 3‐slot schedule
  const xpSchedule = [20, 10, 5];

  // if still have a slot, award next slot
  if (slotCount < xpSchedule.length) {
    return xpSchedule[slotCount];
  }

  // otherwise no XP
  return 0;
}