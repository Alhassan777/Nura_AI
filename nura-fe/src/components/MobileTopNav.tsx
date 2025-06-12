"use client";
import { Flame, Snowflake, Zap } from "lucide-react";
import { Progress } from "antd";
import React from "react";

export const MobileTopNav = () => {
  const level = 12;
  const currentXP = 4450;
  const nextLevelXP = 5000;
  const progressPercentage = Math.floor((currentXP / nextLevelXP) * 100);
  return (
    <div className="sticky top-0 left-0 right-0 z-50 bg-white/30 backdrop-blur-md border-b border-purple-200 h-14 md:hidden shadow-lg shadow-purple-200/50">
      <div className="flex items-center justify-between h-full px-3">
        {/* Freeze and Streak together */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <Snowflake size={18} className="text-blue-500 mr-1" />
            <span className="text-sm font-semibold">4</span>
          </div>
          <div className="flex items-center">
            <Flame size={18} className="text-orange-500 mr-1" />
            <span className="text-sm font-semibold">365</span>
          </div>
        </div>

        {/* Level in the middle with progress circle */}
        <div className="flex items-center justify-center -mt-1 mr-7.5">
          <Progress
            type="circle"
            percent={progressPercentage}
            size={46}
            strokeColor="#8b5cf6"
            trailColor="#f0f0f0"
            strokeWidth={10}
            format={() => (
              <span className="text-xs font-bold text-purple-700">{level}</span>
            )}
          />
        </div>

        {/* XP on the right */}
        <div className="flex items-center">
          <Zap size={18} className="text-yellow-500 mr-1" />
          <span className="text-sm font-semibold">2,450</span>
        </div>
      </div>
    </div>
  );
};

export default MobileTopNav;
