"use client";

import { useState } from "react";
import {
  Card,
  Checkbox,
  Button,
  Tag,
  Modal,
  Input,
  Badge,
  Tooltip,
} from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  HeartOutlined,
  StarOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { formatDistanceToNow } from "date-fns";

interface Memory {
  id: string;
  content: string;
  type: string;
  storage_type: "short_term" | "long_term";
  timestamp: string;
  memory_category?: "short_term" | "long_term" | "emotional_anchor";
  is_meaningful?: boolean;
  is_lasting?: boolean;
  is_symbolic?: boolean;
  relevance_score?: number;
  metadata: {
    [key: string]: any;
  };
  // Computed properties
  is_emotional_anchor?: boolean;
}

interface MemoryCardProps {
  memory: Memory;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onDelete: (memoryId: string) => void;
  onEdit: (memoryId: string, updates: any) => void;
  onConvertToAnchor: (memoryId: string) => void;
}

export const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  isSelected,
  onSelect,
  onDelete,
  onEdit,
  onConvertToAnchor,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(memory.content);

  // Compute is_emotional_anchor from memory_category
  const isEmotionalAnchor =
    memory.memory_category === "emotional_anchor" || memory.is_emotional_anchor;

  const handleSaveEdit = () => {
    if (editedContent.trim() && editedContent !== memory.content) {
      onEdit(memory.id, { content: editedContent.trim() });
    }
    setIsEditing(false);
  };

  const getTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      achievement: "gold",
      relationship: "pink",
      learning: "blue",
      experience: "green",
      goal: "purple",
      reflection: "orange",
    };
    return colors[type] || "default";
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  };

  return (
    <Card
      className={`transition-all duration-200 hover:shadow-md ${
        isSelected ? "ring-2 ring-blue-500 bg-blue-50" : ""
      } ${isEmotionalAnchor ? "border-pink-200 bg-pink-50" : ""}`}
      styles={{ body: { padding: "16px" } }}
    >
      <div className="flex items-start space-x-3">
        {/* Selection Checkbox */}
        <Checkbox
          checked={isSelected}
          onChange={(e) => onSelect(e.target.checked)}
          className="mt-1"
        />

        {/* Memory Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {isEmotionalAnchor ? (
                <Badge.Ribbon text="Emotional Anchor" color="pink">
                  <HeartOutlined className="text-pink-500" />
                </Badge.Ribbon>
              ) : memory.storage_type === "long_term" ||
                memory.memory_category === "long_term" ? (
                <DatabaseOutlined className="text-purple-500" />
              ) : (
                <ClockCircleOutlined className="text-blue-500" />
              )}

              <Tag color={getTypeColor(memory.type)}>{memory.type}</Tag>

              {memory.relevance_score && (
                <Tag color="cyan">
                  {Math.round(memory.relevance_score * 100)}% relevant
                </Tag>
              )}

              {/* Show simplified classification */}
              {memory.memory_category && (
                <Tag
                  color={
                    memory.memory_category === "emotional_anchor"
                      ? "pink"
                      : memory.memory_category === "long_term"
                      ? "purple"
                      : "blue"
                  }
                >
                  {memory.memory_category.replace("_", " ")}
                </Tag>
              )}
            </div>

            <div className="flex items-center space-x-1">
              <Tooltip title="Edit memory">
                <Button
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => setIsEditing(true)}
                />
              </Tooltip>

              {!isEmotionalAnchor && (
                <Tooltip title="Convert to emotional anchor">
                  <Button
                    type="text"
                    size="small"
                    icon={<HeartOutlined />}
                    onClick={() => onConvertToAnchor(memory.id)}
                  />
                </Tooltip>
              )}

              <Tooltip title="Delete memory">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => onDelete(memory.id)}
                />
              </Tooltip>
            </div>
          </div>

          {/* Content */}
          {isEditing ? (
            <div className="space-y-2">
              <Input.TextArea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                rows={3}
                placeholder="Edit memory content..."
              />
              <div className="flex space-x-2">
                <Button type="primary" size="small" onClick={handleSaveEdit}>
                  Save
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    setIsEditing(false);
                    setEditedContent(memory.content);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-gray-700 mb-3 leading-relaxed">
              {memory.content}
            </p>
          )}

          {/* Metadata */}
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>{formatTimestamp(memory.timestamp)}</span>

            <div className="flex items-center space-x-2">
              {memory.metadata?.has_pii && (
                <Tag color="orange">PII Detected</Tag>
              )}

              {memory.metadata?.score && (
                <Tooltip
                  title={`Stability: ${(
                    memory.metadata.score.stability * 100
                  ).toFixed(0)}%`}
                >
                  <StarOutlined className="text-yellow-500" />
                </Tooltip>
              )}

              {/* Show simplified boolean flags */}
              {memory.is_meaningful && <Tag color="green">Meaningful</Tag>}
              {memory.is_lasting && <Tag color="blue">Lasting</Tag>}
              {memory.is_symbolic && <Tag color="purple">Symbolic</Tag>}
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal for mobile or detailed editing */}
      <Modal
        title="Edit Memory"
        open={isEditing}
        onOk={handleSaveEdit}
        onCancel={() => {
          setIsEditing(false);
          setEditedContent(memory.content);
        }}
        okText="Save Changes"
        cancelText="Cancel"
      >
        <Input.TextArea
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          rows={4}
          placeholder="Edit memory content..."
        />
      </Modal>
    </Card>
  );
};
