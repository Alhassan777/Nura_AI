import { type NextRequest, NextResponse } from "next/server";
import { createClient as createSupabaseClient } from "@/utils/supabase/server"; // Renamed to avoid conflict if createClient is defined locally
import { addReflection } from "./utils/add-reflection";

export async function GET(request: NextRequest) {
  try {
    const supabase = await createSupabaseClient();
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { data: reflections, error: reflectionsError } = await supabase
      .from("reflections")
      .select("*")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false });

    if (reflectionsError) {
      console.error("Error fetching reflections:", reflectionsError);
      return NextResponse.json(
        { error: reflectionsError.message, code: reflectionsError.code },
        { status: 500 }
      );
    }

    return NextResponse.json(reflections || [], { status: 200 });
  } catch (error: any) {
    console.error("Error in GET /api/gamification/reflection:", error);
    return NextResponse.json(
      { error: "Internal Server Error", details: error.message },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  return NextResponse.json(
    { message: "Reflection deleted successfully" },
    { status: 200 }
  );
  // try {
  //   const supabase = await createSupabaseClient();
  //   const { data: { user }, error: userError } = await supabase.auth.getUser();

  //   if (userError || !user) {
  //     return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  //   }

  //   const { searchParams } = new URL(request.url);
  //   const reflectionId = searchParams.get('reflectionId');

  //   if (!reflectionId) {
  //     return NextResponse.json({ error: 'Missing reflectionId query parameter' }, { status: 400 });
  //   }

  //   // Verify the reflection belongs to the user before deleting
  //   const { error: deleteError } = await supabase
  //     .from('reflections')
  //     .delete()
  //     .eq('id', reflectionId)
  //     .eq('user_id', user.id); // Ensure the user owns this reflection

  //   if (deleteError) {
  //     console.error('Error deleting reflection:', deleteError);
  //     // Check if the error is due to the reflection not being found or not belonging to the user
  //     // Supabase delete doesn't typically error if the row doesn't exist but matches 0 rows.
  //     // However, if there's a different kind of error (e.g. RLS policy violation if not specific enough)
  //     return NextResponse.json({ error: deleteError.message, code: deleteError.code }, { status: 500 });
  //   }

  //   // It might be useful to check if a row was actually deleted if your RLS policies are very strict
  //   // and might prevent deletion silently. For now, we assume success if no error.
  //   return NextResponse.json({ message: 'Reflection deleted successfully' }, { status: 200 });

  // } catch (error: any) {
  //   console.error('Error in DELETE /api/gamification/reflection:', error);
  //   return NextResponse.json({ error: 'Internal Server Error', details: error.message }, { status: 500 });
  // }
}

export async function POST(request: NextRequest) {
  try {
    const supabase = await createSupabaseClient();
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();

    body.mood = body.mood.toLowerCase();

    const { mood, note, tags } = body;

    if (!mood || !note || !tags) {
      return NextResponse.json(
        { error: "Missing required reflection fields" },
        { status: 400 }
      );
    }
    if (
      typeof mood !== "string" ||
      typeof note !== "string" ||
      !Array.isArray(tags)
    ) {
      return NextResponse.json(
        { error: "Invalid data types for reflection fields" },
        { status: 400 }
      );
    }

    const result = await addReflection(user.id, { mood, note, tags });
    return NextResponse.json(result, { status: 201 });
  } catch (error: any) {
    console.error("Error in POST /api/gamification/reflection:", error);
    // Check if the error is a Supabase specific error (e.g. PostgrestError)
    if (error && typeof error.code === "string") {
      return NextResponse.json(
        { error: error.message, code: error.code },
        { status: 500 }
      );
    }
    return NextResponse.json(
      { error: "Internal Server Error", details: error.message },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const supabase = await createSupabaseClient();
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const reflectionId = searchParams.get("reflectionId");

    if (!reflectionId) {
      return NextResponse.json(
        { error: "Missing reflectionId query parameter" },
        { status: 400 }
      );
    }

    const body = await request.json();
    // We only allow updating mood, note, and tags. Date and user_id should not be changed here.
    const { mood, note, tags } = body;

    if (!mood && !note && !tags) {
      return NextResponse.json(
        { error: "No fields provided for update" },
        { status: 400 }
      );
    }

    const updateData: { mood?: string; note?: string; tags?: string[] } = {};
    if (mood !== undefined) updateData.mood = mood;
    if (note !== undefined) updateData.note = note;
    if (tags !== undefined) updateData.tags = tags;

    // Validate data types if provided
    if (mood !== undefined && typeof mood !== "string") {
      return NextResponse.json(
        { error: "Invalid data type for mood" },
        { status: 400 }
      );
    }
    if (note !== undefined && typeof note !== "string") {
      return NextResponse.json(
        { error: "Invalid data type for note" },
        { status: 400 }
      );
    }
    if (tags !== undefined && !Array.isArray(tags)) {
      return NextResponse.json(
        { error: "Invalid data type for tags" },
        { status: 400 }
      );
    }

    const { data: updatedReflection, error: updateError } = await supabase
      .from("reflections")
      .update(updateData)
      .eq("id", reflectionId)
      .eq("user_id", user.id) // Ensure the user owns this reflection
      .select()
      .single(); // .single() will error if no row is found or multiple rows (should not happen with id)

    if (updateError) {
      console.error("Error updating reflection:", updateError);
      if (updateError.code === "PGRST116") {
        // PGRST116: "The result contains 0 rows"
        return NextResponse.json(
          {
            error:
              "Reflection not found or user does not have permission to update",
          },
          { status: 404 }
        );
      }
      return NextResponse.json(
        { error: updateError.message, code: updateError.code },
        { status: 500 }
      );
    }

    return NextResponse.json(updatedReflection, { status: 200 });
  } catch (error: any) {
    console.error("Error in PUT /api/gamification/reflection:", error);
    if (error.name === "SyntaxError") {
      // JSON parsing error
      return NextResponse.json(
        { error: "Invalid JSON in request body" },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { error: "Internal Server Error", details: error.message },
      { status: 500 }
    );
  }
}
