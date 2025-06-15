import { Modal, Divider } from "antd";
import { Reflection } from "@/services/apis/gamification";
import RecentReflectionItem from "../recent-reflections-card/RecentReflectionItem";
import { MoodSelectorMemo } from "../MoodSelector";

export const ReflectionModals = ({
  isOpen,
  modalTitle,
  reflections,
  onClose,
}: {
  isOpen: boolean;
  modalTitle: string;
  reflections: Reflection[];
  onClose: () => void;
}) => {
  return (
    <Modal
      open={isOpen}
      title={modalTitle}
      onCancel={onClose}
      footer={null}
      width={600}
      className="reflection-modal"
    >
      <MoodSelectorMemo />
      {reflections.length > 0 && <Divider />}
      <div className="space-y-4 max-h-[300px] overflow-y-auto">
        <div className="flex flex-col gap-4">
          {reflections.map((reflection, idx) => (
            <RecentReflectionItem
              key={idx}
              reflection={reflection}
              isLast={idx === reflections.length - 1}
            />
          ))}
        </div>
      </div>
    </Modal>
  );
};

export default ReflectionModals;
