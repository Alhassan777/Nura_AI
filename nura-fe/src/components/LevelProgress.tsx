"use client";

import { Progress } from "antd";

interface LevelProgressProps {
  level: number;
  currentXP: number;
  nextLevelXP: number;
  isCollapsed?: boolean;
}

export default function LevelProgress({
  level,
  currentXP,
  nextLevelXP,
  isCollapsed = false,
}: LevelProgressProps) {
  // Calculate progress percentage
  const progressPercentage = Math.floor((currentXP / nextLevelXP) * 100);
  const xpRemaining = nextLevelXP - currentXP;

  return (
    <div className="mt-6 flex flex-col items-center">
      {!isCollapsed && (
        <h3 className="text-sm font-medium text-gray-500 mb-3 self-start">
          Level Progress
        </h3>
      )}
      <div className="relative flex flex-col items-center">
        <Progress
          type="circle"
          percent={progressPercentage}
          size={isCollapsed ? 60 : 120}
          strokeWidth={10}
          strokeColor="#8b5cf6"
          trailColor="#f0f0f0"
          format={() => (
            <div className="text-center">
              <div
                className={`${
                  isCollapsed ? "text-md" : "text-xl"
                } font-bold text-gray-800`}
              >
                {level}
              </div>
              {!isCollapsed && (
                <div className="text-xs text-gray-500">Level</div>
              )}
            </div>
          )}
        />

        {!isCollapsed && (
          <div className="mt-3 text-center">
            <div className="text-sm font-medium text-gray-700">
              {currentXP.toLocaleString()} / {nextLevelXP.toLocaleString()} XP
            </div>
            <div className="text-xs text-gray-500">
              {xpRemaining.toLocaleString()} XP to next level
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
