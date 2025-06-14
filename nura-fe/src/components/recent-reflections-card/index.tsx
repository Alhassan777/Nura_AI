"use client";
import { Button, Empty, Space } from "antd";
import { AnimatePresence, motion } from "framer-motion";
import RecentReflectionItem from "./RecentReflectionItem";
import { useGetReflections } from "@/services/hooks/use-gamification";
import { ReflectionSkeleton } from "./RecentReflectionSkeleton";

export const RecentReflectionsCard = () => {
  const { data: reflections, isLoading } = useGetReflections();

  const latestThree = reflections?.slice(0, 3);

  console.log("reflections", latestThree);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="bg-white rounded-md shadow-xs border border-gray-200 p-0"
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100 flex items-center justify-between"
      >
        <span>Recent Reflections</span>
        {!isLoading && reflections?.length > 3 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.5 }}
          >
            <Button type="link">View All</Button>
          </motion.div>
        )}
      </motion.div>

      <div className="px-6 pt-4 pb-6">
        {isLoading ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Space direction="vertical" style={{ width: "100%" }}>
              <ReflectionSkeleton />
              <ReflectionSkeleton />
              <ReflectionSkeleton isLast={true} />
            </Space>
          </motion.div>
        ) : latestThree?.length === 0 || !latestThree ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.3 }}
          >
            <Empty description="No reflections yet" />
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <AnimatePresence initial={false}>
              {latestThree?.map((reflection, idx) => (
                <motion.div
                  key={`${reflection.updated_at}-${idx}`}
                  initial={{ opacity: 0, x: -20, scale: 0.95 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: 20, scale: 0.95 }}
                  transition={{
                    duration: 0.4,
                    delay: 0.6 + idx * 0.1,
                    ease: "easeOut",
                  }}
                  whileHover={{
                    scale: 1.02,
                    transition: { duration: 0.2 },
                  }}
                >
                  <RecentReflectionItem
                    reflection={reflection}
                    isLast={idx === latestThree.length - 1}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default RecentReflectionsCard;
