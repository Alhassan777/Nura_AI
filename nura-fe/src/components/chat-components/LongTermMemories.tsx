"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty, Spin, Tag, Space, Button, Modal, Divider, Alert } from "antd";
import { Brain, MessageCircle, Shield, Eye, Trash, Edit } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { MemoryContext } from "./types";

interface LongTermMemoriesProps {
  userId: string;
  conversationId: string;
  isLoadingMemories: boolean;
  memoryContext: MemoryContext | null;
  loadMemories?: () => void;
}

interface PIIItem {
  text: string;
  type: string;
  confidence: number;
  risk_level: string;
}

interface Memory {
  id: string;
  content: string;
  timestamp: string;
  metadata?: {
    memory_category?: string;
    detected_items?: PIIItem[];
    has_pii?: boolean;
    pii_detected?: boolean;
    risk_level?: string;
  };
}

export const LongTermMemories: React.FC<LongTermMemoriesProps> = ({
  userId,
  conversationId,
  isLoadingMemories,
  memoryContext,
  loadMemories,
}) => {
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [showPIIModal, setShowPIIModal] = useState(false);

  const longTermMemories = (memoryContext?.long_term || []) as Memory[];

  const handleViewPII = (memory: Memory) => {
    setSelectedMemory(memory);
    setShowPIIModal(true);
  };

  const handleMemoryAction = (
    memoryId: string,
    action: "keep" | "remove" | "anonymize"
  ) => {
    // TODO: Implement memory consent action
    console.log(`Action ${action} for memory ${memoryId}`);
    setShowPIIModal(false);
    setSelectedMemory(null);
  };

  if (isLoadingMemories) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-green-500" />
            <span>Long-term Memories (This Conversation)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <Spin size="large" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (longTermMemories.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-green-500" />
            <span>Long-term Memories (This Conversation)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            image={<Brain className="mx-auto h-12 w-12 text-green-500" />}
            description={
              <div className="text-center">
                <p className="text-gray-600">No long-term memories yet</p>
                <p className="text-sm text-gray-400">
                  Meaningful and lasting memories will appear here
                </p>
              </div>
            }
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-green-500" />
            <span>Long-term Memories (This Conversation)</span>
            <Tag color="green">{longTermMemories.length}</Tag>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {longTermMemories.map((memory, index) => {
              const hasPII =
                memory.metadata?.has_pii ||
                memory.metadata?.pii_detected ||
                false;
              const detectedItems = memory.metadata?.detected_items || [];

              // Ensure unique keys by combining ID with index and memory type
              const uniqueKey = memory.id
                ? `long-term-${memory.id}-${index}`
                : `long-term-memory-${index}`;

              return (
                <Card key={uniqueKey} className="bg-green-50 border-green-200">
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <MessageCircle className="h-4 w-4 text-green-500 mt-1 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-gray-800 mb-2">{memory.content}</p>

                        {hasPII && (
                          <Alert
                            message="Personal Information Detected"
                            description={`This memory contains ${detectedItems.length} personal information item(s). Click to review and decide what to do with this memory.`}
                            type="warning"
                            showIcon
                            className="mb-3"
                            action={
                              <Button
                                size="small"
                                type="primary"
                                onClick={() => handleViewPII(memory)}
                                icon={<Eye className="h-3 w-3" />}
                              >
                                Review
                              </Button>
                            }
                          />
                        )}

                        <div className="flex items-center justify-between">
                          <Space size="small">
                            <Tag color="green">Long-term</Tag>
                            {memory.metadata?.memory_category && (
                              <Tag color="default">
                                {memory.metadata.memory_category}
                              </Tag>
                            )}
                            {hasPII && (
                              <Tag color="orange">
                                <Shield className="h-3 w-3 mr-1" />
                                PII Detected
                              </Tag>
                            )}
                          </Space>
                          <span className="text-xs text-gray-500">
                            {memory.timestamp
                              ? formatDistanceToNow(
                                  new Date(memory.timestamp),
                                  {
                                    addSuffix: true,
                                  }
                                )
                              : "Recently"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* PII Review Modal */}
      <Modal
        title="Review Personal Information"
        open={showPIIModal}
        onCancel={() => setShowPIIModal(false)}
        footer={null}
        width={600}
      >
        {selectedMemory && (
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Memory Content:</h4>
              <p className="bg-gray-50 p-3 rounded border">
                {selectedMemory.content}
              </p>
            </div>

            {selectedMemory.metadata?.detected_items && (
              <div>
                <h4 className="font-medium mb-2">
                  Detected Personal Information:
                </h4>
                <div className="space-y-2">
                  {selectedMemory.metadata.detected_items.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-orange-50 p-3 rounded border border-orange-200"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-medium">{item.text}</span>
                          <div className="text-sm text-gray-600">
                            Type: {item.type} | Risk: {item.risk_level} |
                            Confidence: {Math.round(item.confidence * 100)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Divider />

            <div>
              <h4 className="font-medium mb-3">
                What would you like to do with this memory?
              </h4>
              <Space direction="vertical" className="w-full">
                <Button
                  type="primary"
                  icon={<Eye className="h-4 w-4" />}
                  onClick={() => handleMemoryAction(selectedMemory.id, "keep")}
                  className="w-full justify-start"
                >
                  Keep memory as-is (including personal information)
                </Button>
                <Button
                  icon={<Edit className="h-4 w-4" />}
                  onClick={() =>
                    handleMemoryAction(selectedMemory.id, "anonymize")
                  }
                  className="w-full justify-start"
                >
                  Keep memory but remove personal information
                </Button>
                <Button
                  danger
                  icon={<Trash className="h-4 w-4" />}
                  onClick={() =>
                    handleMemoryAction(selectedMemory.id, "remove")
                  }
                  className="w-full justify-start"
                >
                  Remove memory entirely
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};
