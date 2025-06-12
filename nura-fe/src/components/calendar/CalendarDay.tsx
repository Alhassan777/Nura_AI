import { Button, Tag } from "antd";
import dayjs, { Dayjs } from "dayjs";
import { MOOD_ICONS } from "@/constants/calendar";
import { memo, useState } from "react";
import { Reflection } from "@/types/reflection";
import { PlusIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import ReflectionModals from "./ReflectionModals";
import { User } from "@supabase/supabase-js";

interface CalendarDayProps {
  date: Dayjs;
  isCurrentMonth: boolean;
  reflections: Reflection[];
  user: User;
}

function CalendarDayComponent({
  date,
  isCurrentMonth,
  reflections,
  user,
}: CalendarDayProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!isCurrentMonth) return null;

  const dayReflections = reflections || [];

  const isToday = date.isSame(new Date(), "day");
  const isPast = date.isBefore(new Date(), "day");
  const isPastUserCreated =
    user?.created_at && date.isBefore(dayjs(user?.created_at), "day");

  const borderState = isToday
    ? "border-purple-400 shadow-sm shadow-purple-100 bg-purple-100/50"
    : dayReflections.length > 0
    ? "border-orange-400 shadow-sm shadow-orange-100 bg-orange-100/50"
    : isPastUserCreated
    ? "border-gray-100 opacity-80 shadow-sm shadow-gray-100 !cursor-not-allowed"
    : isPast
    ? "border-gray-100"
    : "border-red-400 opacity-80 shadow-sm shadow-red-100 !cursor-not-allowed";
  const hoverState = isToday
    ? ""
    : dayReflections.length > 0
    ? "hover:border-orange-400"
    : isPastUserCreated
    ? "hover:border-gray-100"
    : isPast
    ? ""
    : "hover:border-red-500";
  const dateBg = isToday
    ? "bg-purple-100 text-purple-600"
    : dayReflections.length > 0
    ? "bg-orange-100 text-orange-600"
    : isPastUserCreated
    ? "text-gray-500 bg-gray-50 !cursor-not-allowed"
    : isPast
    ? "text-gray-500 bg-gray-50"
    : "text-red-500 bg-red-50";

  return (
    <>
      <div
        className={cn(
          "flex flex-row md:flex-col items-start gap-2 md:items-start backdrop-blur-sm",
          "min-h-[72px] md:min-h-[120px] px-4 md:px-3 py-3",
          "rounded-xl md:rounded-md border transition-all duration-200",
          borderState,
          "cursor-pointer hover:border-purple-400",
          hoverState
        )}
        onClick={() => {
          if (!isPast && !isToday) return;
          if (isPastUserCreated) return;
          setIsOpen(true);
        }}
      >
        <div
          className={cn(
            "w-8 h-8 md:w-7 md:h-7 rounded-full flex items-center justify-center text-sm font-medium mb-0 md:mb-2",
            dateBg
          )}
        >
          {date.date()}
        </div>

        <div
          className={cn(
            "flex-1 flex flex-col gap-2 w-full mt-1.5",
            dayReflections.length === 0 && isPast
              ? "justify-center items-center"
              : ""
          )}
        >
          {dayReflections.slice(0, 2).map((reflection, idx) => (
            <div key={idx} className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2 w-full">
                <span className="flex-shrink-0">
                  {MOOD_ICONS[reflection.mood.toLowerCase()]}
                </span>
                <span className="text-gray-700 text-sm font-medium truncate">
                  {reflection.note}
                </span>
              </div>
              {reflection.tags && reflection.tags.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {reflection.tags.slice(0, 2).map((tag) => (
                    <Tag
                      key={tag.value}
                      color={tag.color}
                      className="!m-0 !text-xs !px-2 !py-0.5 !rounded-md"
                    >
                      {tag.label}
                    </Tag>
                  ))}
                  {reflection.tags.length > 2 && (
                    <span className="text-xs text-gray-400 px-1">
                      +{reflection.tags.length - 2}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}

          {dayReflections.length > 2 && (
            <div className="text-xs font-medium text-purple-500 mt-1">
              +{dayReflections.length - 2} more reflections
            </div>
          )}

          {dayReflections.length === 0 && isPast && !isPastUserCreated && (
            <Button variant="outlined" className="!w-fit">
              <PlusIcon className="w-4 h-4" />
              Add reflection
            </Button>
          )}
        </div>
      </div>
      <ReflectionModals
        isOpen={isOpen}
        onClose={() => {
          console.log("close");
          setIsOpen(false);
        }}
        modalTitle={`${date.format("DD MMM")} Reflections`}
        reflections={dayReflections}
      />
    </>
  );
}

export const CalendarDay = memo(CalendarDayComponent);
