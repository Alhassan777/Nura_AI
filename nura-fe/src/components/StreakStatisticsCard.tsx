"use client";
import { Progress } from "antd";
import { Check } from "lucide-react";
import { useStreakStats } from "@/services/hooks/streak-stats";

export default function StreakStatisticsCard() {
  const { data: stats, isLoading } = useStreakStats();

  if (isLoading) {
    return (
      <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
        <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100 md:text-left text-center">
          Streak Statistics
        </div>
        <div className="flex flex-col md:flex-row justify-between items-center p-0">
          <div className="flex flex-col items-center w-full md:p-0 p-4">
            <div className="w-24 h-24 flex items-center justify-center rounded-full border-6 border-gray-200 mb-2 animate-pulse" />
            <div className="text-gray-900 font-medium mt-1">Loading...</div>
          </div>
          <div className="flex flex-col items-center md:border-l md:border-r md:border-t-0 md:border-b-0 border-t border-b border-gray-200 w-full p-4">
            <div className="w-24 h-24 rounded-full border-6 border-gray-200 animate-pulse" />
            <div className="text-gray-900 font-medium mt-2">Loading...</div>
          </div>
          <div className="flex flex-col items-center w-full md:p-0 p-4">
            <div className="w-24 h-24 rounded-full border-6 border-gray-200 animate-pulse" />
            <div className="text-gray-900 font-medium mt-2">Loading...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100 md:text-left text-center">
        Streak Statistics
      </div>
      <div className="flex flex-col md:flex-row justify-between items-center p-0">
        {/* Current Streak */}
        <div className="flex flex-col items-center w-full md:p-0 p-4">
          <div className="w-24 h-24 flex items-center justify-center rounded-full border-6 border-green-500 mb-2">
            <Check color="#52c41a" size={40} />
          </div>
          <div className="text-gray-900 font-medium mt-1">
            {stats?.currentStreak || 0}-Day Streak
          </div>
        </div>
        {/* 7-Day Progress */}
        <div className="flex flex-col items-center md:border-l md:border-r md:border-t-0 md:border-b-0 border-t border-b border-gray-200 w-full p-4">
          <Progress
            type="circle"
            percent={Math.round(stats?.weekProgress || 0)}
            strokeColor="#9810fa"
            trailColor="#f5f5f5"
            size={90}
            format={(percent) => (
              <span className="text-lg text-gray-900 font-semibold">
                {percent}%
              </span>
            )}
          />
          <div className="text-gray-900 font-medium mt-2">7-Day Progress</div>
        </div>
        {/* 30-Day Journey */}
        <div className="flex flex-col items-center w-full md:p-0 p-4">
          <Progress
            type="circle"
            percent={Math.round(stats?.monthProgress || 0)}
            strokeColor="#9810fa"
            trailColor="#f5f5f5"
            size={90}
            format={(percent) => (
              <span className="text-lg text-gray-900 font-semibold">
                {percent}%
              </span>
            )}
          />
          <div className="text-gray-900 font-medium mt-2">30-Day Journey</div>
        </div>
      </div>
    </div>
  );
}
