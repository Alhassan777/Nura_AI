import FreezeCreditsCard from "./freeze-credits-card";
import QuestsCard from "./quests-card";
import ReflectionsCard from "./reflections-card";
import StreakCard from "./streak-card";
import { StatsCardsProps } from "./type";

export default function StatsCards({ isCollapsed }: StatsCardsProps) {
  return (
    <div className="mt-6">
      {!isCollapsed && (
        <h3 className="text-sm font-medium text-gray-500 mb-3">Your Stats</h3>
      )}
      <div
        className={`grid ${isCollapsed ? "grid-cols-1" : "grid-cols-2"} gap-2`}
      >
        <FreezeCreditsCard isCollapsed={isCollapsed} />
        <QuestsCard isCollapsed={isCollapsed} />
        <StreakCard isCollapsed={isCollapsed} />
        <ReflectionsCard isCollapsed={isCollapsed} />
      </div>
    </div>
  );
}
