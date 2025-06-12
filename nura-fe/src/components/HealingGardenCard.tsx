import { Zap } from "lucide-react";

export default function HealingGardenCard() {
  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0">
      <div className="text-lg font-bold text-gray-900 px-6 pt-6 pb-4 border-b border-gray-100">
        Healing Garden
      </div>
      <div className="flex flex-col items-center px-8 pt-6 pb-2">
        {/* Lucide Zap Icon */}
        <Zap color="#9810fa" size={48} className="mb-2" />
        <div className="text-2xl font-bold text-gray-900 mb-4">
          Level 5 Garden
        </div>
        {/* Main Progress Bar */}
        <div className="w-full flex items-center gap-2 mb-2">
          <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-3 bg-purple-500 rounded-full"
              style={{ width: "75%" }}
            ></div>
          </div>
          <span className="ml-2 text-gray-900 font-medium">75%</span>
        </div>
      </div>
      <div className="text-center text-gray-900 font-medium text-base mb-2">
        Current Quests
      </div>
      <div className="flex flex-col gap-4 px-4 pb-6">
        {/* Quest 1 */}
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="font-semibold text-gray-900 mb-2">
            7-Day Gratitude Challenge
          </div>
          <div className="w-full flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-2 bg-purple-500 rounded-full"
                style={{ width: "40%" }}
              ></div>
            </div>
            <span className="ml-2 text-gray-900 text-sm font-medium">40%</span>
          </div>
        </div>
        {/* Quest 2 */}
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="font-semibold text-gray-900 mb-2">
            Mindful Moments
          </div>
          <div className="w-full flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-2 bg-purple-500 rounded-full"
                style={{ width: "60%" }}
              ></div>
            </div>
            <span className="ml-2 text-gray-900 text-sm font-medium">60%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
