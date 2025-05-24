"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { motion, AnimatePresence } from "framer-motion";
import { useUser } from "@/app/providers";
import { useLocalStorage } from "usehooks-ts";

export interface Reflection {
  id: string;
  date: string;
  title: string;
  mood: "great" | "good" | "neutral" | "bad" | "awful";
  timestamp: number;
  notes: string;
}

// Local storage key for reflections
const REFLECTIONS_STORAGE_KEY = "nura_reflections";

// Helper function to get reflections from local storage
const getStoredReflections = (userId: string): Reflection[] => {
  if (typeof window === "undefined") return [];

  try {
    const stored = localStorage.getItem(`${REFLECTIONS_STORAGE_KEY}_${userId}`);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error("Failed to parse reflections:", error);
    return [];
  }
};

// Helper function to save reflections to local storage
const saveReflections = (userId: string, reflections: Reflection[]) => {
  if (typeof window === "undefined") return;

  try {
    localStorage.setItem(
      `${REFLECTIONS_STORAGE_KEY}_${userId}`,
      JSON.stringify(reflections)
    );
  } catch (error) {
    console.error("Failed to save reflections:", error);
  }
};

// Helper to check if user has reflected today
const hasReflectedToday = (reflections: Reflection[]): boolean => {
  const today = new Date().toISOString().split("T")[0];
  return reflections.some((r) => r.date === today);
};

export function DailyReflection() {
  const { userId, isAuthenticated } = useUser();
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedMood, setSelectedMood] = useState<Reflection["mood"] | null>(
    null
  );
  const [notes, setNotes] = useState("");
  const [reflected, setReflected] = useState(false);
  const [dailyReflection, setDailyReflection] = useLocalStorage<Reflection[]>(
    "daily-reflection",
    []
  );

  // Load reflections from storage
  useEffect(() => {
    if (isAuthenticated) {
      const storedReflections = getStoredReflections(userId);
      setReflections(storedReflections);
      setReflected(hasReflectedToday(storedReflections));
    }
  }, [userId, isAuthenticated]);

  // Save reflection
  const handleSaveReflection = () => {
    if (!selectedMood) return;

    const today = new Date().toISOString().split("T")[0];
    const newReflection: Reflection = {
      id: Date.now().toString(),
      date: today,
      title: "Daily Reflection",
      mood: selectedMood,
      timestamp: Date.now(),
      notes: notes,
    };

    // Add to reflections
    const updatedReflections = [...reflections, newReflection];
    setReflections(updatedReflections);
    saveReflections(userId, updatedReflections);
    setDailyReflection([...dailyReflection, newReflection]);

    // Reset form and close
    setSelectedMood(null);
    setNotes("");
    setIsOpen(false);
    setReflected(true);
  };

  // Reset for a new day
  useEffect(() => {
    const checkNewDay = () => {
      setReflected(hasReflectedToday(reflections));
    };

    // Check at midnight
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);

    const timeUntilMidnight = tomorrow.getTime() - now.getTime();
    const midnightTimeout = setTimeout(checkNewDay, timeUntilMidnight);

    return () => clearTimeout(midnightTimeout);
  }, [reflections]);

  // Mood options with emojis
  const moodOptions = [
    { value: "great", emoji: "😄", label: "Great" },
    { value: "good", emoji: "🙂", label: "Good" },
    { value: "neutral", emoji: "😐", label: "Okay" },
    { value: "bad", emoji: "😔", label: "Low" },
    { value: "awful", emoji: "😢", label: "Awful" },
  ];

  if (!isAuthenticated) return null;

  return (
    <div className="fixed bottom-6 left-6 z-50">
      <AnimatePresence>
        {isOpen ? (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="mb-2 w-80"
          >
            <Card className="backdrop-blur-md bg-background/90 dark:bg-card/90 border-neutral-200/20 dark:border-neutral-800/50 shadow-lg">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-medium">
                  Daily Reflection
                </CardTitle>
                <CardDescription>How are you feeling today?</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  {moodOptions.map((mood) => (
                    <Button
                      key={mood.value}
                      type="button"
                      variant={
                        selectedMood === mood.value ? "outline" : "ghost"
                      }
                      className={`px-2 py-1 h-full transition-all duration-200 ${
                        selectedMood === mood.value
                          ? "!bg-foreground !text-background"
                          : ""
                      }`}
                      onClick={() =>
                        setSelectedMood(mood.value as Reflection["mood"])
                      }
                    >
                      <div className="flex flex-col items-center">
                        <span className="text-2xl">{mood.emoji}</span>
                        <span className="text-xs mt-1">{mood.label}</span>
                      </div>
                    </Button>
                  ))}
                </div>

                <div>
                  <Textarea
                    value={notes}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                      setNotes(e.target.value)
                    }
                    placeholder="Add any notes about your day... (optional)"
                    className="min-h-[80px] resize-none"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveReflection}
                  disabled={!selectedMood}
                  size="sm"
                >
                  Save Reflection
                </Button>
              </CardFooter>
            </Card>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <Button
        variant={reflected ? "ghost" : "outline"}
        onClick={() => setIsOpen(!isOpen)}
        className={`rounded-full shadow-lg ${
          reflected
            ? "bg-primary/10 hover:bg-primary/20 border-primary/30"
            : "animate-pulse border-dashed border-2 border-primary/50"
        }`}
      >
        {reflected ? (
          <div className="flex items-center">
            <span className="text-lg mr-2">✓</span>
            <span className="text-sm">Reflected</span>
          </div>
        ) : (
          <div className="flex items-center">
            <span className="text-lg mr-2">📝</span>
            <span className="text-sm">Daily Check-in</span>
          </div>
        )}
      </Button>
    </div>
  );
}
