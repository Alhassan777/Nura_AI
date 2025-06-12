import { useState } from "react";
import { Button, Input, Modal, Select, Tag, Tooltip } from "antd";
import { CloseOutlined, PlusOutlined } from "@ant-design/icons";
import { useLocalStorage } from "usehooks-ts";
import { TagType } from "@/types/tag";
import { defaultTags, antdColors } from "@/constants/tags";

interface TagSelectorProps {
  value: TagType[];
  onChange: (value: TagType[]) => void;
  placeholder?: string;
}

export function TagSelector({
  value,
  onChange,
  placeholder = "Select tags",
}: TagSelectorProps) {
  const [customTags, setCustomTags] = useLocalStorage<TagType[]>(
    "custom_tags",
    []
  );

  const [modalOpen, setModalOpen] = useState(false);
  const [newTagLabel, setNewTagLabel] = useState("");
  const [newTagColor, setNewTagColor] = useState("blue");

  const allTags: TagType[] = [...defaultTags, ...customTags];

  const triggerAdd = () => {
    if (!newTagLabel.trim()) return;
    const tag: TagType = {
      label: newTagLabel.trim(),
      value: newTagLabel.trim(),
      color: newTagColor,
    };
    setCustomTags([...customTags, tag]);
    onChange([...value, tag]);
    setNewTagLabel("");
    setNewTagColor("blue");
    setModalOpen(false);
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1 font-medium text-gray-700">
        <span>Tags</span>
        <Tooltip title="Add new tag">
          <Button
            type="text"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          />
        </Tooltip>
      </div>
      <Select
        mode="multiple"
        style={{ width: "100%" }}
        placeholder={placeholder}
        value={value?.map((t) => t.value) || []}
        onChange={(vals) => {
          const selected = allTags.filter((t) => vals.includes(t.value));
          onChange(selected);
        }}
      >
        {allTags.map((tag) => (
          <Select.Option key={tag.value} value={tag.value}>
            <div className="flex items-center gap-2">
              <Tag color={tag.color}>{tag.label}</Tag>
            </div>
          </Select.Option>
        ))}
      </Select>

      <Modal
        title="Add New Tag"
        open={modalOpen}
        okText="Add"
        onOk={triggerAdd}
        okButtonProps={{ disabled: !newTagLabel.trim() }}
        onCancel={() => setModalOpen(false)}
      >
        <div className="flex flex-col gap-4">
          <Input
            placeholder="Tag label"
            value={newTagLabel}
            onChange={(e) => setNewTagLabel(e.target.value)}
          />
          <Select value={newTagColor} onChange={setNewTagColor}>
            {antdColors.map((color) => (
              <Select.Option key={color} value={color}>
                <Tag color={color}>{color}</Tag>
              </Select.Option>
            ))}
          </Select>
        </div>
      </Modal>
    </div>
  );
}
