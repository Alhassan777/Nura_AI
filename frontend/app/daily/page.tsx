"use client";
import React, { useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { useReadLocalStorage } from "usehooks-ts";
import { Reflection } from "@/components/DailyReflection";
import { MOOD_OPTIONS } from "@/constant";
import { MoodAnalysisDialog } from "@/components/MoodAnalysisDialog";
import { DailyReflectionDialog } from "@/components/DailyReflectionDialog";

export default function Page() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const dailyReflection =
    useReadLocalStorage<Reflection[]>("daily-reflection") || [];
  const [dialogDate, setDialogDate] = useState<string | null>(null);
  const [reflections, setReflections] = useState(dailyReflection);

  // Get the first entry date
  const firstEntryDate =
    dailyReflection.length > 0
      ? new Date(
          Math.min(
            ...dailyReflection.map((ref) => new Date(ref.date).getTime())
          )
        )
      : new Date();

  // Update local storage and state on save
  const handleSaveReflection = (reflection: Reflection) => {
    let updated: Reflection[];
    if (reflections.some((r) => r.id === reflection.id)) {
      updated = reflections.map((r) =>
        r.id === reflection.id ? reflection : r
      );
    } else {
      updated = [...reflections, reflection];
    }
    setReflections(updated);
    localStorage.setItem("daily-reflection", JSON.stringify(updated));
  };

  const handleDeleteReflection = (reflection: Reflection) => {
    const updated = reflections.filter((r) => r.id !== reflection.id);
    setReflections(updated);
    localStorage.setItem("daily-reflection", JSON.stringify(updated));
  };

  return (
    <div className="p-4 space-y-4">
      <MoodAnalysisDialog dailyReflection={reflections} />
      <DailyReflectionDialog
        isOpen={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        reflections={reflections.filter((r) => r.date === dialogDate)}
        date={dialogDate}
        onSave={handleSaveReflection}
        onDelete={handleDeleteReflection}
      />
      <FullCalendar
        plugins={[dayGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        events={reflections}
        dayMaxEvents={2}
        headerToolbar={false}
        eventContent={(arg) => {
          const mood = MOOD_OPTIONS.find(
            (mood) => mood.value === arg.event.extendedProps.mood
          );
          return (
            <div className="flex items-center gap-2 w-full">
              <div className="text-2xl">{mood?.emoji}</div>
              <div className="text-sm truncate">
                {mood?.label} - {arg.event.extendedProps.notes}
              </div>
            </div>
          );
        }}
        dateClick={(info) => {
          const clickedDate = new Date(info.date);
          const firstDate = new Date(firstEntryDate);
          const today = new Date();
          today.setHours(0, 0, 0, 0);

          if (clickedDate < firstDate || clickedDate > today) {
            return;
          }
          setDialogDate(info.dateStr);
          setIsDialogOpen(true);
        }}
        dayCellClassNames={(arg) => {
          const date = new Date(arg.date);
          const firstDate = new Date(firstEntryDate);
          const today = new Date();
          today.setHours(0, 0, 0, 0);

          if (date < firstDate || date > today) {
            return "fc-day-disabled";
          }

          return "";
        }}
      />
    </div>
  );
}
