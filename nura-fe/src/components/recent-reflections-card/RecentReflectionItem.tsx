import { message, Tag, TagType } from "antd";
import { motion } from "framer-motion";
import { MOOD_OPTIONS } from "@/constants/calendar";
import React, { useState } from "react";
import { Reflection } from "@/types/reflection";
import { PencilIcon, TrashIcon } from "lucide-react";
import { Button, Popconfirm } from "antd";
import EditReflectionModal from "./EditReflectionModal";
import { useDeleteReflection } from "@/services/hooks/use-gamification";
import { useInvalidateQueries } from "@/services/apis/invalidate-queries";

export const RecentReflectionItem = ({
  reflection,
  isLast,
}: {
  reflection: Reflection;
  isLast: boolean;
}) => {
  console.log("reflection", reflection);

  const SelectedMood = MOOD_OPTIONS.find(
    (m) => m.key.toLowerCase() === reflection.mood.toLowerCase()
  );

  const { mutateAsync: deleteReflection, isPending: isDeleting } =
    useDeleteReflection();

  const { invalidateReflectionsQuery } = useInvalidateQueries();

  const [editModalOpen, setEditModalOpen] = useState(false);

  if (!SelectedMood) return null;

  return (
    <>
      <motion.div
        key={reflection.updated_at}
        layout
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{
          opacity: 0,
          x: 50,
          height: 0,
          marginTop: 0,
          marginBottom: 0,
          padding: 0,
        }}
        transition={{ duration: 0.25 }}
        className="flex gap-3 relative"
      >
        {/* Icon and vertical line */}
        <div className="flex flex-col items-center">
          <span className="mb-1">{SelectedMood.icon}</span>
          {!isLast && (
            <span className="block w-px flex-1 bg-gray-200 mt-1 mb-1"></span>
          )}
        </div>
        <div
          className={`flex-1 ${
            !isLast ? "pb-4 border-b border-gray-100 mb-4" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="font-semibold text-gray-900">
              {new Date(reflection.created_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
            <div className="mt-2 flex gap-3">
              <Button
                size="small"
                onClick={() => {
                  setEditModalOpen(true);
                }}
              >
                <PencilIcon className="w-4 h-4" />
              </Button>
              <Popconfirm
                title="Are you sure delete this reflection?"
                okType="danger"
                okButtonProps={{ loading: isDeleting }}
                cancelButtonProps={{ disabled: isDeleting }}
                onConfirm={async () => {
                  try {
                    await deleteReflection({ reflectionId: reflection.id });
                    invalidateReflectionsQuery();
                    message.success("Reflection deleted");
                  } catch (error) {
                    console.error(error);
                    message.error("Failed to delete reflection");
                  }
                }}
              >
                <Button size="small" danger>
                  <TrashIcon className="w-4 h-4" />
                </Button>
              </Popconfirm>
            </div>
          </div>
          <div className="text-gray-600 mt-1 mb-2 whitespace-pre-line">
            {reflection.note}
          </div>
          <div className="flex gap-2 flex-wrap">
            {reflection?.tags?.map((t) => (
              <Tag key={t.value} color={t.color}>
                {t.label}
              </Tag>
            ))}
          </div>
        </div>
      </motion.div>
      <EditReflectionModal
        selectedReflection={reflection}
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
      />
    </>
  );
};

export default RecentReflectionItem;
