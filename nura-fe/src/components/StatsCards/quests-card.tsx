import { SquareCheck } from "lucide-react";
import { useQuests } from "@/services/hooks/use-quests";
import SkeletonCard from "./skeleton-card";
import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";

export const QuestsCard = ({ isCollapsed }: { isCollapsed: boolean }) => {
  const { data: quests, isLoading } = useQuests();

  const allQuests = [
    ...(quests?.systemQuests || []),
    ...(quests?.userQuests || []),
  ];

  if (isLoading) return <SkeletonCard isCollapsed={isCollapsed} />;

  const completedQuests =
    allQuests?.filter((quest) => quest.progress.completed).length || 0;
  const totalQuests = allQuests?.length || 0;

  return (
    <motion.div
      className="bg-green-50 border border-green-200 rounded-lg p-3 flex flex-col items-center justify-center shadow-sm !shadow-green-200 truncate"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <SquareCheck className="!text-green-500 text-xl mb-1" />
      </motion.div>
      {!isCollapsed && (
        <span className="text-sm font-medium text-gray-700">Quests</span>
      )}
      <span
        className={`${
          isCollapsed ? "text-sm" : "text-lg"
        } font-bold text-green-600 text-center w-full`}
      >
        <AnimatedNumber value={completedQuests} className="inline" />
        /
        <AnimatedNumber value={totalQuests} className="inline" />
      </span>
    </motion.div>
  );
};

export default QuestsCard;
