"use client";
import { Zap } from "lucide-react";
import { useUser } from "@/services/hooks/user";
import { useQuests } from "@/services/hooks/use-quests";
import { getLevelProgress } from "@/utils/level-system";
import { motion } from "framer-motion";

// Skeleton Loading Component
const HealingGardenSkeleton = () => {
  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0 animate-pulse">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100">
        <div className="h-6 bg-gray-200 rounded w-32"></div>
      </div>
      <div className="flex flex-col items-center px-8 pt-6 pb-2">
        {/* Icon skeleton */}
        <div className="w-12 h-12 bg-gray-200 rounded-full mb-2"></div>
        {/* Level text skeleton */}
        <div className="h-8 bg-gray-200 rounded w-40 mb-4"></div>
        {/* Progress bar skeleton */}
        <div className="w-full flex items-center gap-2 mb-2">
          <div className="flex-1 h-3 bg-gray-200 rounded-full"></div>
          <div className="w-10 h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
      <div className="text-center text-gray-900 font-medium text-base mb-2">
        <div className="h-5 bg-gray-200 rounded w-28 mx-auto"></div>
      </div>
      <div className="flex flex-col gap-4 px-4 pb-6">
        {/* Quest skeletons */}
        {[1, 2].map((i) => (
          <div
            key={i}
            className="bg-white rounded-xl border border-gray-100 p-4"
          >
            <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="w-full flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full"></div>
              <div className="w-8 h-4 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function HealingGardenCard() {
  const { data: user, isLoading: userLoading } = useUser();
  const { data: quests, isLoading: questsLoading } = useQuests();

  const isLoading = userLoading || questsLoading;

  const levelProgress = user
    ? getLevelProgress(user.xp)
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

  if (isLoading) {
    return <HealingGardenSkeleton />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="bg-white rounded-md shadow-xs border border-gray-200 p-0"
    >
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100">
        Healing Garden
      </div>
      <div className="flex flex-col items-center px-8 pt-6 pb-2">
        {/* Animated Zap Icon */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{
            duration: 0.6,
            delay: 0.2,
            type: "spring",
            stiffness: 200,
            damping: 15,
          }}
        >
          <Zap color="#9810fa" size={48} className="mb-2" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="text-2xl font-bold text-gray-900 mb-4"
        >
          Level {levelProgress.currentLevel} Garden
        </motion.div>

        {/* Animated Main Progress Bar */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="w-full flex items-center gap-2 mb-2"
        >
          <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${levelProgress.progressPercentage}%` }}
              transition={{
                duration: 1.2,
                delay: 0.6,
                ease: "easeInOut",
              }}
              className="h-3 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
            />
          </div>
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 1.0 }}
            className="ml-2 text-gray-900 font-medium"
          >
            {levelProgress.progressPercentage}%
          </motion.span>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.5 }}
        className="text-center text-gray-900 font-medium text-base mb-2"
      >
        Current Quests
      </motion.div>

      <div className="flex flex-col gap-4 px-4 pb-6">
        {activeQuests.slice(0, 2).map((quest, index) => {
          const questProgress =
            ((quest.progress.count || 0) / quest.frequency) * 100;

          return (
            <motion.div
              key={quest.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                duration: 0.5,
                delay: 0.7 + index * 0.1,
                ease: "easeOut",
              }}
              whileHover={{
                scale: 1.02,
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              }}
              className="bg-white rounded-xl border border-gray-100 p-4 transition-all duration-200"
            >
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.8 + index * 0.1 }}
                className="font-semibold text-gray-900 mb-2"
              >
                {quest.title}
              </motion.div>

              <div className="w-full flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${questProgress}%` }}
                    transition={{
                      duration: 1.0,
                      delay: 0.9 + index * 0.1,
                      ease: "easeInOut",
                    }}
                    className="h-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
                  />
                </div>
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 1.2 + index * 0.1 }}
                  className="ml-2 text-gray-900 text-sm font-medium"
                >
                  {Math.floor(questProgress)}%
                </motion.span>
              </div>
            </motion.div>
          );
        })}

        {activeQuests.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.7 }}
            className="text-center text-gray-500 py-4"
          >
            No active quests at the moment
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
