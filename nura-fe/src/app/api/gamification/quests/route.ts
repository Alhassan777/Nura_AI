import { NextResponse } from "next/server";
import { createQuest, getUserQuests, completeQuest } from "./utils";

export async function GET() {
  try {
    const quests = await getUserQuests();
    return NextResponse.json(quests);
  } catch (error) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const { title, description, time_frame, frequency, xp_reward } =
    await request.json();
  const quest = await createQuest({
    title,
    description,
    time_frame,
    frequency,
    xp_reward,
  });
  return NextResponse.json(quest);
}

export async function PUT(request: Request) {
  try {
    const { questId } = await request.json();
    const result = await completeQuest(questId);
    return NextResponse.json(result);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
}