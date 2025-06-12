"use client";

import { useState, useEffect } from "react";
import { Button, Input, App as AntdApp } from "antd";
import { Smile, Frown, Meh, Heart, Laugh, Angry } from "lucide-react";
import { MoodSelector } from "@/components/MoodSelector";

const moods = [
  { label: "Great", color: "#52c41a", icon: Laugh },
  { label: "Good", color: "#9810fa", icon: Smile },
  { label: "Natural", color: "#8c8c8c", icon: Meh },
  { label: "Bad", color: "#fa541c", icon: Frown },
  { label: "Very Sad", color: "#f5222d", icon: Angry },
];

const moodIcons = {
  Great: Laugh,
  Good: Smile,
  Natural: Meh,
  Bad: Frown,
  "Very Sad": Angry,
};

function getTodayKey() {
  const today = new Date();
  return `reflection-${today.getFullYear()}-${
    today.getMonth() + 1
  }-${today.getDate()}`;
}

export default function TodaysMoodCard() {
  const [selected, setSelected] = useState<string | undefined>(undefined);
  const selectedMood = moods.find((m) => m.label === selected) || moods[0];
  const IconComponent =
    moodIcons[selectedMood.label as keyof typeof moodIcons] || Laugh;

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-8 w-full flex flex-col items-center gap-6">
      <IconComponent size={64} strokeWidth={2} color={selectedMood.color} />
      <div className="text-2xl font-bold text-gray-900 text-center">
        Today's Mood
      </div>
      <div className="flex flex-col items-center gap-4 w-full">
        <MoodSelector onChange={setSelected} />
      </div>
    </div>
  );
}
