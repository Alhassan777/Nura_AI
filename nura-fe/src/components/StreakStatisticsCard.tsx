"use client";
import { Progress } from "antd";
import { Check } from "lucide-react";

export default function StreakStatisticsCard() {
  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100 md:text-left text-center">
        Streak Statistics
      </div>
      <div className="flex flex-col md:flex-row justify-between items-center p-0">
        {/* 3-Day Streak */}
        <div className="flex flex-col items-center w-full md:p-0 p-4">
          <div className="w-24 h-24 flex items-center justify-center rounded-full border-6 border-green-500 mb-2">
            <Check color="#52c41a" size={40} />
          </div>
          <div className="text-gray-900 font-medium mt-1">3-Day Streak</div>
        </div>
        {/* 7-Day Progress */}
        <div className="flex flex-col items-center md:border-l md:border-r md:border-t-0 md:border-b-0 border-t border-b border-gray-200 w-full p-4">
          <Progress
            type="circle"
            percent={85}
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
            percent={60}
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
