import { MOOD_OPTIONS } from "@/constants/calendar";
import { Input, message, Modal, Select } from "antd";
import React, { useState } from "react";
import { TagSelector } from "../common/TagSelector";
import { Reflection } from "@/types/reflection";
import { useUpdateReflection } from "@/services/hooks/use-gamification";
import { useInvalidateQueries } from "@/services/apis/invalidate-queries";

export const EditReflectionModal = ({
  selectedReflection,
  isOpen,
  onClose,
}: {
  selectedReflection: Reflection | null;
  isOpen: boolean;
  onClose: () => void;
}) => {
  const [editReflection, setEditReflection] = useState<Reflection | null>(
    selectedReflection || null
  );

  const { mutateAsync: updateReflection, isPending: isUpdating } =
    useUpdateReflection();

  const { invalidateReflectionsQuery } = useInvalidateQueries();

  if (!editReflection) return null;

  return (
    <Modal
      title="Edit Reflection"
      open={isOpen}
      onOk={async () => {
        try {
          await updateReflection({
            reflectionId: editReflection.id,
            reflection: editReflection,
          });
          await invalidateReflectionsQuery();
          message.success("Reflection updated");
          onClose();
        } catch (error) {
          console.error(error);
          message.error("Failed to save reflection");
        }
      }}
      onCancel={onClose}
      okText="Save"
      width={500}
      okButtonProps={{ loading: isUpdating }}
      cancelButtonProps={{ disabled: isUpdating }}
    >
      <div className="flex flex-col gap-4">
        <div>
          <div className="mb-1 font-medium">Mood</div>
          <Select
            value={editReflection.mood || ""}
            onChange={(val) =>
              setEditReflection({ ...editReflection, mood: val || "" })
            }
            style={{ width: "100%" }}
          >
            {MOOD_OPTIONS.map((m) => (
              <Select.Option key={m.key} value={m.key}>
                <div className="flex items-center gap-2">
                  {m.icon}
                  <span>{m.label}</span>
                </div>
              </Select.Option>
            ))}
          </Select>
        </div>
        <div>
          <div className="mb-1 font-medium">Note</div>
          <Input.TextArea
            rows={3}
            value={editReflection.note || ""}
            onChange={(e) =>
              setEditReflection({
                ...editReflection,
                note: e.target.value || "",
              })
            }
            maxLength={200}
            showCount
          />
        </div>
        <div>
          <TagSelector
            value={editReflection.tags || []}
            onChange={(tags) => setEditReflection({ ...editReflection, tags })}
          />
        </div>
      </div>
    </Modal>
  );
};

export default EditReflectionModal;
