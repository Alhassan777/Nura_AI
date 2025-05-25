import React from "react";
import { Reflection } from "@/components/DailyReflection";

interface StreakCounterProps {
  reflections: Reflection[];
}

function getCurrentStreak(dates: Date[]): number {
  if (!dates.length) return 0;
  dates.sort((a, b) => b.getTime() - a.getTime());
  let streak = 0;
  let current = new Date();
  current.setHours(0, 0, 0, 0);
  for (let i = 0; i < dates.length; i++) {
    if (dates[i].toDateString() === current.toDateString()) {
      streak++;
      current.setDate(current.getDate() - 1);
    } else {
      break;
    }
  }
  return streak;
}

function getBestStreak(dates: Date[]): number {
  if (!dates.length) return 0;
  dates.sort((a, b) => a.getTime() - b.getTime());
  let best = 1;
  let current = 1;
  for (let i = 1; i < dates.length; i++) {
    const prev = new Date(dates[i - 1]);
    const curr = new Date(dates[i]);
    prev.setHours(0, 0, 0, 0);
    curr.setHours(0, 0, 0, 0);
    const diff = (curr.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24);
    if (diff === 1) {
      current++;
      best = Math.max(best, current);
    } else if (diff > 1) {
      current = 1;
    }
  }
  return best;
}

export function StreakCounter({ reflections }: StreakCounterProps) {
  const dates = reflections.map((r) => new Date(r.date));
  const currentStreak = getCurrentStreak([...dates]);
  const bestStreak = getBestStreak([...dates]);

  return (
    <div className="flex flex-col items-center gap-2 p-4 bg-muted rounded-lg shadow">
      <div className="flex gap-8">
        <div className="flex flex-col items-center">
          <span className="text-sm font-medium">Current Streak</span>
          <span className="text-2xl font-bold text-amber-500 flex items-center">
            {currentStreak} <span className="ml-1">🔥</span>
          </span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-sm font-medium">Best Streak</span>
          <span className="text-2xl font-bold text-green-600 flex items-center">
            {bestStreak} <span className="ml-1">🏆</span>
          </span>
        </div>
      </div>
      <div className="text-xs text-muted-foreground mt-2">
        Keep your streak going for extra motivation!
      </div>
    </div>
  );
}
