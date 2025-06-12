import { Skeleton } from "antd";

export const ReflectionSkeleton = ({
  isLast = false,
}: {
  isLast?: boolean;
}) => {
  return (
    <div className="flex gap-3 relative">
      {/* Icon and vertical line */}
      <div className="flex flex-col items-center">
        <Skeleton.Avatar active size="small" className="mb-1" />
        {!isLast && (
          <span className="block w-px flex-1 bg-gray-200 mt-1 mb-1"></span>
        )}
      </div>
      <div
        className={`flex-1 ${
          !isLast ? "pb-4 border-b border-gray-100 mb-4" : ""
        }`}
      >
        <div className="flex items-center justify-between">
          <Skeleton.Button active size="small" style={{ width: 150 }} />
          <div className="mt-2 flex gap-3">
            <Skeleton.Button active size="small" style={{ width: 32 }} />
            <Skeleton.Button active size="small" style={{ width: 32 }} />
          </div>
        </div>
        <div className="text-gray-600 mt-1 mb-2">
          <Skeleton active paragraph={{ rows: 2 }} title={false} />
        </div>
        <div className="flex gap-2 flex-wrap">
          <Skeleton.Button active size="small" style={{ width: 60 }} />
          <Skeleton.Button active size="small" style={{ width: 70 }} />
          <Skeleton.Button active size="small" style={{ width: 65 }} />
        </div>
      </div>
    </div>
  );
};
