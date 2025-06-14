"use client";
import { Zap } from "lucide-react";
import { useUser } from "@/services/hooks/user";
import { useQuests } from "@/services/hooks/use-quests";
import { getLevelProgress } from "@/utils/level-system";

export default function HealingGardenCard() {
  const { data: user } = useUser();
  const { data: quests } = useQuests();

  const levelProgress = user
    ? getLevelProgress(user.xp, user.xp)
    : {
        currentLevel: 1,
        progressPercentage: 0,
        xpNeededForNextLevel: 100,
      };

  // Combine system and user quests, filter out completed ones
  const activeQuests = [
    ...(quests?.systemQuests?.filter((quest) => !quest.progress.completed) ||
      []),
    ...(quests?.userQuests?.filter((quest) => !quest.progress.completed) || []),
  ];

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100">
        Healing Garden
      </div>
      <div className="flex flex-col items-center px-8 pt-6 pb-2">
        {/* Lucide Zap Icon */}
        <Zap color="#9810fa" size={48} className="mb-2" />
        <div className="text-2xl font-bold text-gray-900 mb-4">
          Level {levelProgress.currentLevel} Garden
        </div>
        {/* Main Progress Bar */}
        <div className="w-full flex items-center gap-2 mb-2">
          <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-3 bg-purple-500 rounded-full"
              style={{ width: `${levelProgress.progressPercentage}%` }}
            ></div>
          </div>
          <span className="ml-2 text-gray-900 font-medium">
            {levelProgress.progressPercentage}%
          </span>
        </div>
      </div>
      <div className="text-center text-gray-900 font-medium text-base mb-2">
        Current Quests
      </div>
      <div className="flex flex-col gap-4 px-4 pb-6">
        {activeQuests.slice(0, 2).map((quest) => (
          <div
            key={quest.id}
            className="bg-white rounded-xl border border-gray-100 p-4"
          >
            <div className="font-semibold text-gray-900 mb-2">
              {quest.title}
            </div>
            <div className="w-full flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-2 bg-purple-500 rounded-full"
                  style={{
                    width: `${
                      ((quest.progress.count || 0) / quest.frequency) * 100
                    }%`,
                  }}
                ></div>
              </div>
              <span className="ml-2 text-gray-900 text-sm font-medium">
                {Math.floor(
                  ((quest.progress.count || 0) / quest.frequency) * 100
                )}
                %
              </span>
            </div>
          </div>
        ))}
        {activeQuests.length === 0 && (
          <div className="text-center text-gray-500 py-4">
            No active quests at the moment
          </div>
        )}
      </div>
    </div>
  );
}
