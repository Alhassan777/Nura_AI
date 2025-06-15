// src/services/badges.ts
import { NextResponse } from "next/server";
import { getBadgesGroupedByType } from "./utils";

export async function GET() {
  try {
    const grouped = await getBadgesGroupedByType();
    return NextResponse.json(grouped);
  } catch (err: Error | unknown) {
    const errorMessage = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
