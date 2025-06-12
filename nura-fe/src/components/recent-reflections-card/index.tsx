"use client";
import { Button, Empty, Space } from "antd";
import { AnimatePresence } from "framer-motion";
import RecentReflectionItem from "./RecentReflectionItem";
import { useGetReflections } from "@/services/hooks/use-gamification";
import { ReflectionSkeleton } from "./RecentReflectionSkeleton";

export const RecentReflectionsCard = () => {
  const { data: reflections, isLoading } = useGetReflections();

  const latestThree = reflections?.slice(0, 3);

  console.log("reflections", latestThree);

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100 flex items-center justify-between">
        <span>Recent Reflections</span>
        {!isLoading && reflections?.length > 3 && (
          <Button type="link">View All</Button>
        )}
      </div>
      <div className="px-6 pt-4 pb-6">
        {isLoading ? (
          <Space direction="vertical" style={{ width: "100%" }}>
            <ReflectionSkeleton />
            <ReflectionSkeleton />
            <ReflectionSkeleton isLast={true} />
          </Space>
        ) : latestThree?.length === 0 || !latestThree ? (
          <Empty description="No reflections yet" />
        ) : (
          <AnimatePresence initial={false}>
            {latestThree?.map((reflection, idx) => (
              <RecentReflectionItem
                key={`${reflection.updated_at}-${idx}`}
                reflection={reflection}
                isLast={idx === latestThree.length - 1}
              />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default RecentReflectionsCard;
