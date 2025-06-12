import React from "react";
import TodaysMoodCard from "@/components/TodaysMoodCard";
import { RecentReflectionsCard } from "@/components/recent-reflections-card";
import HealingGardenCard from "@/components/HealingGardenCard";
import StreakStatisticsCard from "@/components/StreakStatisticsCard";
import ChatWithNuraCard from "@/components/ChatWithNuraCard";
import ReflectionCalendarCard from "@/components/ReflectionCalendarCard";
import FeaturesGridCard from "@/components/FeaturesGridCard";

export default function Page() {
  return (
    <div className="w-full flex flex-col gap-4 py-6">
      <div className="flex md:flex-row flex-col gap-4">
        <div className="flex flex-col gap-4 w-full">
          <TodaysMoodCard />
          <StreakStatisticsCard />
        </div>
        <div className="flex flex-col gap-4 w-full">
          <ReflectionCalendarCard />
          <RecentReflectionsCard />
        </div>
        <div className="flex flex-col gap-4 w-full">
          <ChatWithNuraCard />
          <HealingGardenCard />
        </div>
      </div>
      <FeaturesGridCard />
    </div>
  );
}
