import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "antd";
import { MONTHS } from "@/constants/calendar";

interface CalendarHeaderProps {
  viewMonth: number;
  viewYear: number;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onToday: () => void;
}

export function CalendarHeader({
  viewMonth,
  viewYear,
  onPrevMonth,
  onNextMonth,
  onToday,
}: CalendarHeaderProps) {
  return (
    <div className="sticky md:top-4 top-18 backdrop-blur-xs bg-white/20 border border-purple-200 shadow-lg shadow-purple-100 z-10 flex flex-wrap items-center gap-2 sm:gap-4 mb-6 w-full p-2 rounded-lg">
      <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
        <button
          className="rounded-l px-2 py-1 bg-white hover:bg-gray-50 cursor-pointer"
          onClick={onPrevMonth}
          aria-label="Previous Month"
        >
          <ChevronLeft size={20} />
        </button>
        <button
          className="rounded-r px-2 py-1 bg-white hover:bg-gray-50 -ml-px cursor-pointer"
          onClick={onNextMonth}
          aria-label="Next Month"
        >
          <ChevronRight size={20} />
        </button>
      </div>
      <div className="text-xl sm:text-2xl font-bold mx-2">
        {MONTHS[viewMonth]} {viewYear}
      </div>

      <Button
        className="ml-auto flex items-center gap-2"
        type="primary"
        onClick={onToday}
      >
        <CalendarIcon size={18} /> Today
      </Button>
    </div>
  );
}
