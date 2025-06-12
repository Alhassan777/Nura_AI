import { createClient as createSupabaseClient } from "@/utils/supabase/server";
import { validateReflectionXp } from "./validate-reflection-xp";

export async function awardXp(userId: string, fallbackAmount: number, event_type: string): Promise<number> {

  const amount = event_type === 'reflection'
    ? await validateReflectionXp(userId)
    : fallbackAmount;

  if (amount <= 0) {
    return 0;  // nothing to do
  }

  console.log(`Awarding ${amount} XP to ${userId} for ${event_type}`);
  const supabase = await createSupabaseClient();
  const { data: profile, error: profileError } = await supabase
    .from('users')
    .select('xp')
    .eq('id', userId)
    .single();

  if (profileError) {
    console.error("Error fetching user profile for XP:", profileError);
    return 0;
  }

  const currentXp = profile?.xp || 0;
  const newXpTotal = currentXp + amount;

  const { error: updateError } = await supabase
    .from('users')
    .update({ xp: newXpTotal })
    .eq('id', userId);

  const { error: xpError } = await supabase
    .from('xp_events')
    .insert({
      user_id: userId,
      amount,
      event_type,
    });

  if (updateError || xpError) {
    console.error("Error updating user XP:", updateError || xpError);
    return currentXp;
  }
  return newXpTotal;
}