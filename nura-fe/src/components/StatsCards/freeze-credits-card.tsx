import { Snowflake } from "lucide-react";
import SkeletonCard from "./skeleton-card";
import { useUser } from "@/services/hooks/user";
import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";

export const FreezeCreditsCard = ({
  isCollapsed,
}: {
  isCollapsed: boolean;
}) => {
  const { data: user, isLoading } = useUser();

  if (isLoading) return <SkeletonCard isCollapsed={isCollapsed} />;

  return (
    <motion.div
      className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex flex-col items-center justify-center shadow-sm !shadow-blue-200"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <Snowflake className="!text-blue-500 text-xl mb-1" />
      </motion.div>
      {!isCollapsed && (
        <span className="text-sm font-medium text-gray-700">Freeze</span>
      )}
      <AnimatedNumber
        value={user?.freeze_credits || 0}
        className={`${
          isCollapsed ? "text-sm" : "text-lg"
        } font-bold text-blue-600`}
      />
    </motion.div>
  );
};

export default FreezeCreditsCard;
