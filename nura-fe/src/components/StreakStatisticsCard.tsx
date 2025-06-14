"use client";
import { Progress } from "antd";
import { Check } from "lucide-react";
import { useStreakStats } from "@/services/hooks/streak-stats";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function StreakStatisticsCard() {
  const { data: stats, isLoading } = useStreakStats();
  const [animatedWeekProgress, setAnimatedWeekProgress] = useState(0);
  const [animatedMonthProgress, setAnimatedMonthProgress] = useState(0);

  // Animate progress values when data loads
  useEffect(() => {
    if (stats && !isLoading) {
      const weekTarget = Math.round(stats.weekProgress || 0);
      const monthTarget = Math.round(stats.monthProgress || 0);

      // Animate week progress
      const weekTimer = setInterval(() => {
        setAnimatedWeekProgress((prev) => {
          if (prev >= weekTarget) {
            clearInterval(weekTimer);
            return weekTarget;
          }
          return Math.min(prev + 2, weekTarget);
        });
      }, 20);

      // Animate month progress with slight delay
      setTimeout(() => {
        const monthTimer = setInterval(() => {
          setAnimatedMonthProgress((prev) => {
            if (prev >= monthTarget) {
              clearInterval(monthTimer);
              return monthTarget;
            }
            return Math.min(prev + 2, monthTarget);
          });
        }, 20);
      }, 300);

      return () => {
        clearInterval(weekTimer);
      };
    }
  }, [stats, isLoading]);

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
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Progress
              type="circle"
              percent={animatedWeekProgress}
              strokeColor="#9810fa"
              trailColor="#f5f5f5"
              size={90}
              format={(percent) => (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                  className="text-lg text-gray-900 font-semibold"
                >
                  {percent}%
                </motion.span>
              )}
            />
          </motion.div>
          <div className="text-gray-900 font-medium mt-2">7-Day Progress</div>
        </div>
        {/* 30-Day Journey */}
        <div className="flex flex-col items-center w-full md:p-0 p-4">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Progress
              type="circle"
              percent={animatedMonthProgress}
              strokeColor="#9810fa"
              trailColor="#f5f5f5"
              size={90}
              format={(percent) => (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.7 }}
                  className="text-lg text-gray-900 font-semibold"
                >
                  {percent}%
                </motion.span>
              )}
            />
          </motion.div>
          <div className="text-gray-900 font-medium mt-2">30-Day Journey</div>
        </div>
      </div>
    </div>
  );
}
