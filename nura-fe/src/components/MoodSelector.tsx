import { Button, Input, message, Divider, Tooltip } from "antd";
import React, { useEffect, useState, memo } from "react";
import { TagSelector } from "@/components/common/TagSelector";
import { TagType } from "@/types/tag";
import { MOOD_OPTIONS } from "@/constants/calendar";
import {
  DEFAULT_REFLECTION,
  DefaultReflection,
} from "@/constants/default-reflection";
import { useCreateReflection } from "@/services/hooks/use-gamification";
// Removed invalidate queries - using React Query's built-in invalidation

export function MoodSelector({
  onChange,
}: {
  onChange?: (mood: string) => void;
}) {
  const { mutateAsync: addReflection, isPending: isAdding } =
    useCreateReflection();

  // React Query automatically invalidates queries in useCreateReflection

  const [currentReflection, setCurrentReflection] =
    useState<DefaultReflection>(DEFAULT_REFLECTION);

  const handleSave = async () => {
    try {
      const reflectionData = {
        mood: currentReflection.mood,
        note: currentReflection.note,
        tags: currentReflection.tags.map((tag) =>
          typeof tag === "string" ? tag : tag.label
        ),
      };
      await addReflection(reflectionData);
      message.success("Reflection saved!");
    } catch (error) {
      console.error(error);
      message.error("Failed to save reflection");
    }
  };

  useEffect(() => {
    onChange?.(currentReflection.mood);
  }, [currentReflection.mood, onChange]);

  return (
    <div className="flex flex-col items-center gap-6 w-full">
      <div className="flex flex-col items-center gap-2 w-full">
        <div className="text-lg font-semibold text-gray-900 mb-1">
          How are you feeling today?
        </div>
        <div className="flex flex-row gap-3 justify-center w-full">
          {MOOD_OPTIONS.map((moodOption) => {
            const isActive = currentReflection.mood === moodOption.label;
            return (
              <Tooltip
                key={moodOption.label}
                title={moodOption.label}
                placement="top"
              >
                <Button
                  shape="circle"
                  size="large"
                  style={{
                    background: isActive ? moodOption.color + "22" : undefined,
                    borderColor: isActive ? moodOption.color : undefined,
                    color: moodOption.color,
                    transition: "all 0.2s",
                    boxShadow: isActive
                      ? `0 8px 15px -5px ${moodOption.color}`
                      : undefined,
                  }}
                  className={`flex items-center justify-center`}
                  onClick={() =>
                    setCurrentReflection({
                      ...currentReflection,
                      mood: moodOption.label,
                    })
                  }
                >
                  {moodOption.icon}
                </Button>
              </Tooltip>
            );
          })}
        </div>
      </div>
      <Divider className="!my-2" />
      <TagSelector
        value={currentReflection.tags as TagType[]}
        onChange={(tags) =>
          setCurrentReflection({ ...currentReflection, tags })
        }
      />
      <Divider className="!my-2" />
      <div className="w-full">
        <div className="mb-1 font-medium text-gray-700">Reflection</div>
        <Input.TextArea
          rows={3}
          placeholder="Add a note about your mood..."
          value={currentReflection.note}
          onChange={(e) =>
            setCurrentReflection({
              ...currentReflection,
              note: e.target.value,
            })
          }
          className="!rounded-lg !resize-none"
          maxLength={200}
          showCount
          style={{ fontSize: 16 }}
        />
      </div>
      <Button
        type="primary"
        className="mt-2 w-full !rounded-lg !font-semibold !text-base"
        onClick={handleSave}
        size="large"
        loading={isAdding}
      >
        {isAdding ? "Saving..." : "Save Reflection"}
      </Button>
    </div>
  );
}

export const MoodSelectorMemo = memo(MoodSelector);
