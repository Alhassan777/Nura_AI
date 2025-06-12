import { NextResponse } from "next/server";
import { getUserQuests } from "./utils";

export async function GET() {
  try {
    const quests = await getUserQuests();
    return NextResponse.json(quests);
  } catch (error) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}