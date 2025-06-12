"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Button,
  Tag,
  Modal,
  message,
  Alert,
  Empty,
  Space,
  Tooltip,
  Badge,
} from "antd";
import {
  WarningOutlined,
  EyeOutlined,
  DeleteOutlined,
  EditOutlined,
  SafetyOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { formatDistanceToNow } from "date-fns";
import {
  usePendingConsentMemories,
  useProcessPendingConsent,
} from "@/services/hooks/use-memory";

interface PendingMemory {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  memory_category: string;
  consent_options: any;
  pii_summary: {
    detected_types: string[];
    items_count: number;
  };
}

interface PendingConsentMemoriesProps {
  userId?: string;
}

export const PendingConsentMemories: React.FC<PendingConsentMemoriesProps> = ({
  userId,
}) => {
  const [selectedChoices, setSelectedChoices] = useState<
    Record<string, string>
  >({});
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});

  const { data: pendingData, isLoading, refetch } = usePendingConsentMemories();

  const { mutateAsync: processConsentMutation, isPending: isProcessing } =
    useProcessPendingConsent();

  const pendingMemories = pendingData?.pending_memories || [];
  const totalCount = pendingData?.total_count || 0;

  const handleChoiceChange = (memoryId: string, choice: string) => {
    setSelectedChoices((prev) => ({
      ...prev,
      [memoryId]: choice,
    }));
  };

  const toggleDetails = (memoryId: string) => {
    setShowDetails((prev) => ({
      ...prev,
      [memoryId]: !prev[memoryId],
    }));
  };

  const getChoiceColor = (choice: string) => {
    switch (choice) {
      case "approve":
        return "success";
      case "deny":
        return "error";
      case "anonymize":
        return "warning";
      default:
        return "default";
    }
  };

  const getChoiceIcon = (choice: string) => {
    switch (choice) {
      case "approve":
        return "✓";
      case "deny":
        return "✗";
      case "anonymize":
        return "🔒";
      default:
        return "?";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  };

  const handleProcessChoices = async () => {
    const choicesWithDefaults = { ...selectedChoices };

    // Set default action for memories without explicit choice
    pendingMemories.forEach((memory: PendingMemory) => {
      if (!choicesWithDefaults[memory.id]) {
        choicesWithDefaults[memory.id] = "deny"; // Default to deny if no choice made
      }
    });

    try {
      const memoryChoices: Record<string, any> = {};

      Object.entries(choicesWithDefaults).forEach(([memoryId, action]) => {
        memoryChoices[memoryId] = {
          action,
          consent: action === "approve" ? {} : undefined, // Add proper consent structure if needed
        };
      });

      await processConsentMutation(memoryChoices);

      message.success(
        `Processed ${Object.keys(memoryChoices).length} pending memories`
      );
      setSelectedChoices({});
    } catch (error) {
      console.error("Error processing pending consent:", error);
      message.error("Failed to process pending memories. Please try again.");
    }
  };

  const hasAnyChoices = Object.keys(selectedChoices).length > 0;
  const allChoicesMade =
    pendingMemories.length > 0 &&
    pendingMemories.every(
      (memory: PendingMemory) => selectedChoices[memory.id]
    );

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading pending memories...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (totalCount === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <SafetyOutlined className="h-5 w-5 text-green-500" />
            <span>Privacy Consent</span>
            <Badge count={0} showZero className="ml-2" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            image={
              <SafetyOutlined className="mx-auto h-12 w-12 text-green-500" />
            }
            description={
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  All caught up!
                </h3>
                <p className="text-gray-600">
                  No memories are currently waiting for your privacy consent.
                </p>
              </div>
            }
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-orange-200 bg-orange-50">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <WarningOutlined className="h-5 w-5 text-orange-500" />
            <span>Memories Awaiting Privacy Consent</span>
            <Badge count={totalCount} className="ml-2" />
          </div>

          {hasAnyChoices && (
            <Button
              type="primary"
              onClick={handleProcessChoices}
              loading={isProcessing}
              disabled={!allChoicesMade}
            >
              Process Decisions ({Object.keys(selectedChoices).length}/
              {totalCount})
            </Button>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <Alert
          message="Privacy Review Required"
          description="These memories contain personal information and need your consent before being stored long-term. Choose how you'd like each memory to be handled."
          type="warning"
          showIcon
          className="mb-4"
        />

        <div className="space-y-4">
          {pendingMemories.map((memory: PendingMemory) => (
            <Card
              key={memory.id}
              className={`${
                selectedChoices[memory.id] ? "ring-2 ring-blue-500" : ""
              }`}
            >
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Memory Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <ClockCircleOutlined className="text-gray-500" />
                      <span className="text-sm text-gray-500">
                        {formatTimestamp(memory.timestamp)}
                      </span>
                      <Tag color="blue">{memory.type}</Tag>

                      {memory.memory_category && (
                        <Tag color="purple">
                          {memory.memory_category.replace("_", " ")}
                        </Tag>
                      )}
                    </div>

                    <Button
                      type="text"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => toggleDetails(memory.id)}
                    >
                      {showDetails[memory.id] ? "Hide" : "Show"} PII Details
                    </Button>
                  </div>

                  {/* Memory Content */}
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-gray-700">{memory.content}</p>
                  </div>

                  {/* PII Information */}
                  <div className="flex items-center space-x-2">
                    <SafetyOutlined className="text-orange-500" />
                    <span className="text-sm text-gray-600">
                      Contains {memory.pii_summary.items_count} personal
                      information item(s):
                    </span>
                    <div className="flex space-x-1">
                      {memory.pii_summary.detected_types.map((type) => (
                        <Tag key={type} color="orange">
                          {type}
                        </Tag>
                      ))}
                    </div>
                  </div>

                  {/* PII Details (when expanded) */}
                  {showDetails[memory.id] && memory.consent_options && (
                    <div className="p-3 bg-blue-50 rounded-lg text-sm">
                      <h4 className="font-medium mb-2">
                        Detected Personal Information:
                      </h4>
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(memory.consent_options, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Choice Buttons */}
                  <div className="flex space-x-2 pt-2">
                    <Tooltip title="Keep memory exactly as written, including personal information">
                      <Button
                        type={
                          selectedChoices[memory.id] === "approve"
                            ? "primary"
                            : "default"
                        }
                        onClick={() => handleChoiceChange(memory.id, "approve")}
                        className={
                          selectedChoices[memory.id] === "approve"
                            ? "bg-green-500 border-green-500"
                            : ""
                        }
                      >
                        ✓ Keep Original
                      </Button>
                    </Tooltip>

                    <Tooltip title="Remove personal information but keep the rest of the memory">
                      <Button
                        type={
                          selectedChoices[memory.id] === "anonymize"
                            ? "primary"
                            : "default"
                        }
                        onClick={() =>
                          handleChoiceChange(memory.id, "anonymize")
                        }
                        className={
                          selectedChoices[memory.id] === "anonymize"
                            ? "bg-yellow-500 border-yellow-500"
                            : ""
                        }
                      >
                        🔒 Remove PII
                      </Button>
                    </Tooltip>

                    <Tooltip title="Delete this memory completely">
                      <Button
                        type={
                          selectedChoices[memory.id] === "deny"
                            ? "primary"
                            : "default"
                        }
                        danger={selectedChoices[memory.id] === "deny"}
                        onClick={() => handleChoiceChange(memory.id, "deny")}
                      >
                        ✗ Delete Memory
                      </Button>
                    </Tooltip>
                  </div>

                  {/* Selected Choice Indicator */}
                  {selectedChoices[memory.id] && (
                    <div className="flex items-center space-x-2 pt-2 border-t">
                      <span className="text-sm text-gray-600">
                        Your choice:
                      </span>
                      <Tag color={getChoiceColor(selectedChoices[memory.id])}>
                        {getChoiceIcon(selectedChoices[memory.id])}{" "}
                        {selectedChoices[memory.id] === "approve"
                          ? "Keep Original"
                          : selectedChoices[memory.id] === "anonymize"
                          ? "Remove PII"
                          : "Delete Memory"}
                      </Tag>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bottom Action Bar */}
        {pendingMemories.length > 0 && (
          <div className="mt-6 p-4 bg-white rounded-lg border">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {Object.keys(selectedChoices).length} of {totalCount} memories
                have decisions
              </div>

              <Space>
                <Button
                  onClick={() => setSelectedChoices({})}
                  disabled={!hasAnyChoices}
                >
                  Clear All Choices
                </Button>

                <Button
                  type="primary"
                  onClick={handleProcessChoices}
                  loading={isProcessing}
                  disabled={!allChoicesMade}
                >
                  Apply All Decisions
                </Button>
              </Space>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
