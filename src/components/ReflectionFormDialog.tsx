import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Reflection } from "@/components/DailyReflection";
import { MOOD_OPTIONS } from "@/constant";

interface ReflectionFormDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  selectedDate: string | null;
  selectedMood: Reflection["mood"] | null;
  notes: string;
  onMoodChange: (mood: Reflection["mood"]) => void;
  onNotesChange: (notes: string) => void;
  onSubmit: () => void;
}

export function ReflectionFormDialog({
  isOpen,
  onOpenChange,
  selectedDate,
  selectedMood,
  notes,
  onMoodChange,
  onNotesChange,
  onSubmit,
}: ReflectionFormDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Reflection for {selectedDate}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex justify-between">
            {MOOD_OPTIONS.map((mood) => (
              <Button
                key={mood.value}
                type="button"
                variant={selectedMood === mood.value ? "default" : "ghost"}
                className={`px-2 py-1 h-full transition-all duration-200 ${
                  selectedMood === mood.value
                    ? "bg-primary/10 text-primary"
                    : ""
                }`}
                onClick={() => onMoodChange(mood.value as Reflection["mood"])}
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
              onChange={(e) => onNotesChange(e.target.value)}
              placeholder="Add any notes about your day... (optional)"
              className="min-h-[80px] resize-none"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={onSubmit} disabled={!selectedMood}>
              Save Reflection
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
