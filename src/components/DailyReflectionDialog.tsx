import React, { useState } from "react";
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
import { Edit, Trash2 } from "lucide-react";

interface DailyReflectionDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  reflections: Reflection[];
  date: string | null;
  onSave: (reflection: Reflection) => void;
  onDelete?: (reflection: Reflection) => void;
}

export function DailyReflectionDialog({
  isOpen,
  onOpenChange,
  reflections,
  date,
  onSave,
  onDelete,
}: DailyReflectionDialogProps) {
  const [mode, setMode] = useState<"list" | "form">("list");
  const [editReflection, setEditReflection] = useState<Reflection | null>(null);
  const [selectedMood, setSelectedMood] = useState<Reflection["mood"] | null>(
    null
  );
  const [notes, setNotes] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const moodMap = Object.fromEntries(MOOD_OPTIONS.map((m) => [m.value, m]));

  // Open form for new or existing reflection
  const openForm = (reflection?: Reflection) => {
    setEditReflection(reflection || null);
    setSelectedMood(reflection?.mood || null);
    setNotes(reflection?.notes || "");
    setMode("form");
  };

  // Save handler
  const handleSave = () => {
    if (!date || !selectedMood) return;
    const reflection: Reflection = editReflection
      ? { ...editReflection, mood: selectedMood, notes }
      : {
          id: Date.now().toString(),
          date,
          title: "Daily Reflection",
          mood: selectedMood,
          timestamp: Date.now(),
          notes,
        };
    onSave(reflection);
    setMode("list");
  };

  // Delete handler
  const handleDelete = () => {
    if (editReflection && onDelete) {
      onDelete(editReflection);
      setShowDeleteConfirm(false);
      setMode("list");
    }
  };

  // Reset state when dialog opens/closes or date changes
  React.useEffect(() => {
    setMode("list");
    setEditReflection(null);
    setSelectedMood(null);
    setNotes("");
    setShowDeleteConfirm(false);
  }, [isOpen, date]);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {mode === "list"
              ? `Reflections for ${date}`
              : editReflection
              ? "Edit Reflection"
              : "Add Reflection"}
          </DialogTitle>
        </DialogHeader>
        {mode === "list" ? (
          <div className="space-y-4">
            {reflections.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No reflections for this day.
              </div>
            ) : (
              reflections.map((reflection) => (
                <div
                  key={reflection.id}
                  className="flex items-center gap-3 border-b pb-3 last:border-b-0 last:pb-0 cursor-pointer hover:bg-accent p-2 rounded-md"
                  onClick={() => openForm(reflection)}
                >
                  <div className="text-2xl">
                    {moodMap[reflection.mood]?.emoji}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">
                      {moodMap[reflection.mood]?.label}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {reflection.notes || (
                        <span className="italic">No notes</span>
                      )}
                    </div>
                  </div>
                  <div className="text-muted-foreground">
                    <Edit className="h-4 w-4" />
                  </div>
                </div>
              ))
            )}
            <Button className="w-full mt-2" onClick={() => openForm()}>
              Add Reflection
            </Button>
          </div>
        ) : (
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
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any notes about your day... (optional)"
                className="min-h-[80px] resize-none"
              />
            </div>
            <div className="flex flex-col justify-between gap-2 w-full">
              <div className="flex justify-between gap-2 w-full">
                <Button
                  className="flex-1"
                  variant="outline"
                  onClick={() => setMode("list")}
                >
                  Back
                </Button>
                {editReflection && onDelete && (
                  <Button
                    variant="destructive"
                    onClick={() => setShowDeleteConfirm(true)}
                    className="flex items-center gap-1"
                  >
                    <Trash2 className="h-4 w-4" /> Delete
                  </Button>
                )}
              </div>
              <Button onClick={handleSave} disabled={!selectedMood}>
                Save Reflection
              </Button>
            </div>
            {showDeleteConfirm && (
              <div className="bg-destructive/10 border border-destructive text-destructive rounded p-3 mt-2 flex flex-col items-center">
                <div>Are you sure you want to delete this reflection?</div>
                <div className="flex gap-2 mt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowDeleteConfirm(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleDelete}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
