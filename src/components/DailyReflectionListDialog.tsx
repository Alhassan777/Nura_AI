import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Reflection } from "@/components/DailyReflection";
import { MOOD_OPTIONS } from "@/constant";

interface DailyReflectionListDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  reflections: Reflection[];
  date: string | null;
}

export function DailyReflectionListDialog({
  isOpen,
  onOpenChange,
  reflections,
  date,
}: DailyReflectionListDialogProps) {
  const moodMap = Object.fromEntries(MOOD_OPTIONS.map((m) => [m.value, m]));
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Reflections for {date}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {reflections.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No reflections for this day.
            </div>
          ) : (
            reflections.map((reflection) => (
              <div
                key={reflection.id}
                className="flex items-start gap-3 border-b pb-3 last:border-b-0 last:pb-0"
              >
                <div className="text-2xl">
                  {moodMap[reflection.mood]?.emoji}
                </div>
                <div>
                  <div className="font-medium">
                    {moodMap[reflection.mood]?.label}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {reflection.notes || (
                      <span className="italic">No notes</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
