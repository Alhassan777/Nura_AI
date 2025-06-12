import { NextResponse } from "next/server";
import { createClient } from "@/utils/supabase/server";

export async function GET() {
  try {
    const supabase = await createClient();
    const { data: { user }, error: userError } = await supabase.auth.getUser();

    if (userError) {
      console.error("Error fetching user:", userError);
      return NextResponse.json(
        { error: "Error fetching user data" },
        { status: 500 }
      );
    }

    if (!user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Get additional profile data from database if you have a profiles table
    // This is just an example - modify according to your actual schema
    const { data: profile, error: profileError } = await supabase
      .from('users')
      .select('*')
      .eq('id', user.id)
      .single();

    const { data: reflections, error: reflectionsError } = await supabase
      .from('reflections')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (profileError && profileError.code !== 'PGRST116') { // PGRST116: No rows returned (which is fine if user has no profile yet)
      console.error("Error fetching profile:", profileError);
    }

    // Prepare the response with user information
    const userData = {
      id: user.id,
      email: user.email,
      emailVerified: !!user.email_confirmed_at,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
      lastSignInAt: user.last_sign_in_at,
      metadata: user.user_metadata,
      profile: profile || null,
      current_streak: profile?.current_streak || 0,
      xp: profile?.xp || 0,
      freeze_credits: profile?.freeze_credits || 0,
      reflections: reflections || null,
    };

    return NextResponse.json(userData, { status: 200 });
  } catch (error: unknown) {
    console.error("Unexpected error in user API:", error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: "Internal server error", details: errorMessage },
      { status: 500 }
    );
  }
} 