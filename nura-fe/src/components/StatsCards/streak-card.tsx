import { Flame } from "lucide-react";
import { useUser } from "@/services/hooks/user";
import SkeletonCard from "./skeleton-card";
import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";

export const StreakCard = ({ isCollapsed }: { isCollapsed: boolean }) => {
  const { data: user, isLoading } = useUser();

  if (isLoading) return <SkeletonCard isCollapsed={isCollapsed} />;

  return (
    <motion.div
      className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex flex-col items-center justify-center shadow-sm !shadow-orange-200"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <Flame className="text-xl mb-1 !text-orange-500" />
      </motion.div>
      {!isCollapsed && (
        <span className="text-sm font-medium text-gray-700">Streak</span>
      )}
      <AnimatedNumber
        value={user?.current_streak || 0}
        className={`${
          isCollapsed ? "text-sm" : "text-lg"
        } font-bold text-orange-600`}
        suffix={isCollapsed ? "" : " days"}
      />
    </motion.div>
  );
};

export default StreakCard;
