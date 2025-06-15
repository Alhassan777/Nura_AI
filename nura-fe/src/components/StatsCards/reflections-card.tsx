import { useReflections } from "@/services/hooks/use-gamification";
import { CommentOutlined } from "@ant-design/icons";
import SkeletonCard from "./skeleton-card";
import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";

export const ReflectionsCard = ({ isCollapsed }: { isCollapsed: boolean }) => {
  const { data: reflections, isLoading } = useReflections();

  if (isLoading) return <SkeletonCard isCollapsed={isCollapsed} />;

  return (
    <motion.div
      className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex flex-col items-center justify-center shadow-sm !shadow-purple-200"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <CommentOutlined className="!text-purple-500 text-xl mb-1" />
      </motion.div>
      {!isCollapsed && (
        <span className="text-sm font-medium text-gray-700">Reflection</span>
      )}
      <AnimatedNumber
        value={reflections?.length || 0}
        className={`${
          isCollapsed ? "text-sm" : "text-lg"
        } font-bold text-purple-600`}
      />
    </motion.div>
  );
};

export default ReflectionsCard;
