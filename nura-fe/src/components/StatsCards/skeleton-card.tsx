import React from "react";

export const SkeletonCard = ({ isCollapsed }: { isCollapsed: boolean }) => {
  return (
    <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 flex flex-col items-center justify-center shadow-sm animate-pulse">
      <div className="w-5 h-5 rounded-full bg-gray-200 mb-1"></div>
      {!isCollapsed && (
        <div className="w-16 h-4 bg-gray-200 rounded mb-1"></div>
      )}
      <div
        className={`w-10 h-${isCollapsed ? "4" : "6"} bg-gray-200 rounded`}
      ></div>
    </div>
  );
};

export default SkeletonCard;
