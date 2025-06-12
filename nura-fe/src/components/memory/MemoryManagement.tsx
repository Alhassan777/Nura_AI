"use client";

import React, { useState } from "react";
import {
  Card,
  List,
  Switch,
  Button,
  Tag,
  Typography,
  Space,
  Modal,
  Alert,
  Input,
  Tooltip,
  Badge,
  Empty,
  Spin,
} from "antd";
import {
  Eye,
  EyeOff,
  Trash2,
  Shield,
  User,
  Calendar,
  Lock,
  Unlock,
  Search,
  Filter,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { useMemories, useDeleteMemory } from "../../services/hooks";
import { useQueryClient } from "@tanstack/react-query";

const { Text, Paragraph } = Typography;
const { Search: SearchInput } = Input;

interface BackendMemory {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  metadata?: {
    storage_type?: string;
    has_pii?: boolean;
    detected_items?: string[];
    score?: {
      relevance?: number;
      stability?: number;
      explicitness?: number;
    };
  };
}

interface MemoryManagementProps {
  memoryType: "short-term" | "long-term" | "anchors";
}

// PII detection function
const detectPII = (content: string): string[] => {
  const piiPatterns = [
    { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, type: "SSN" },
    { pattern: /\b\d{3}-\d{3}-\d{4}\b/g, type: "Phone" },
    {
      pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      type: "Email",
    },
    {
      pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
      type: "Credit Card",
    },
    { pattern: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, type: "Name" },
  ];

  const detected: string[] = [];
  piiPatterns.forEach(({ pattern, type }) => {
    if (pattern.test(content)) {
      detected.push(type);
    }
  });

  return detected;
};

export const MemoryManagement: React.FC<MemoryManagementProps> = ({
  memoryType,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [privacyStates, setPrivacyStates] = useState<Record<string, boolean>>(
    {}
  );

  const queryClient = useQueryClient();
  const { data: memories = [], isLoading, refetch } = useMemories(memoryType);
  const deleteMemoryMutation = useDeleteMemory();

  // Convert backend memories to a more usable format
  const convertedMemories = (memories as BackendMemory[]).map((memory) => ({
    ...memory,
    piiDetected: memory.metadata?.detected_items || detectPII(memory.content),
    isPrivate: privacyStates[memory.id] ?? false,
    score: memory.metadata?.score?.relevance || 0.5,
    category: memory.type,
  }));

  const filteredMemories = convertedMemories.filter(
    (memory) =>
      memory.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      memory.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const togglePrivacy = (memoryId: string) => {
    setPrivacyStates((prev) => ({
      ...prev,
      [memoryId]: !prev[memoryId],
    }));
  };

  const deleteMemory = (memoryId: string) => {
    Modal.confirm({
      title: "Delete Memory",
      content:
        "Are you sure you want to delete this memory? This action cannot be undone.",
      okText: "Delete",
      okType: "danger",
      onOk() {
        deleteMemoryMutation.mutate(memoryId, {
          onSuccess: () => {
            // Refetch memories after deletion
            queryClient.invalidateQueries({
              queryKey: ["memories", memoryType],
            });
          },
        });
      },
    });
  };

  const removePII = (memoryId: string) => {
    // For now, this just updates the local display
    // In a real implementation, you'd call an API to update the memory content
    const memory = convertedMemories.find((m) => m.id === memoryId);
    if (!memory) return;

    let cleanContent = memory.content;
    const piiPatterns = [
      { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: "[SSN REMOVED]" },
      { pattern: /\b\d{3}-\d{3}-\d{4}\b/g, replacement: "[PHONE REMOVED]" },
      {
        pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
        replacement: "[EMAIL REMOVED]",
      },
      {
        pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
        replacement: "[CARD REMOVED]",
      },
      {
        pattern: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g,
        replacement: "[NAME REMOVED]",
      },
    ];

    piiPatterns.forEach(({ pattern, replacement }) => {
      cleanContent = cleanContent.replace(pattern, replacement);
    });

    Modal.info({
      title: "PII Removal Preview",
      content: (
        <div>
          <Text strong>Original:</Text>
          <Paragraph>{memory.content}</Paragraph>
          <Text strong>After PII Removal:</Text>
          <Paragraph>{cleanContent}</Paragraph>
          <Text type="secondary">
            Note: In a full implementation, this would update the actual memory
            content.
          </Text>
        </div>
      ),
    });
  };

  const getTypeTitle = () => {
    switch (memoryType) {
      case "short-term":
        return "Short-term Memory";
      case "long-term":
        return "Long-term Memory";
      case "anchors":
        return "Emotional Anchors";
    }
  };

  const getTypeDescription = () => {
    switch (memoryType) {
      case "short-term":
        return "Recent memories that may contain temporary information";
      case "long-term":
        return "Important memories stored for extended periods";
      case "anchors":
        return "Emotional anchors that provide stability and grounding";
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
        <Text className="ml-3">Loading memories...</Text>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <Card
        title={
          <div className="flex justify-between items-center">
            <div>
              <Text strong className="text-lg">
                {getTypeTitle()}
              </Text>
              <br />
              <Text type="secondary" className="text-sm">
                {getTypeDescription()}
              </Text>
            </div>
            <Button
              icon={<RefreshCw className="h-4 w-4" />}
              onClick={handleRefresh}
              loading={isLoading}
            >
              Refresh
            </Button>
          </div>
        }
        className="flex-1"
        classNames={{
          body: "!p-0 h-full",
        }}
      >
        <div className="p-4 border-b">
          <SearchInput
            placeholder="Search memories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-4"
          />

          <Space size="small" wrap>
            <Badge count={convertedMemories.length} showZero>
              <Tag icon={<User className="h-3 w-3" />}>Total</Tag>
            </Badge>
            <Badge
              count={
                convertedMemories.filter((m) => m.piiDetected.length > 0).length
              }
              showZero
            >
              <Tag icon={<Shield className="h-3 w-3" />} color="orange">
                Contains PII
              </Tag>
            </Badge>
            <Badge
              count={convertedMemories.filter((m) => m.isPrivate).length}
              showZero
            >
              <Tag icon={<Lock className="h-3 w-3" />} color="red">
                Private
              </Tag>
            </Badge>
          </Space>
        </div>

        <div className="flex-1 overflow-auto">
          {filteredMemories.length === 0 ? (
            <Empty
              description={
                memories.length === 0
                  ? `No ${memoryType.replace("-", " ")} memories yet`
                  : "No memories match your search"
              }
              className="mt-8"
            />
          ) : (
            <List
              dataSource={filteredMemories}
              renderItem={(memory) => (
                <List.Item className="!border-b !border-gray-100 !px-4 !py-3">
                  <div className="w-full">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Text strong className="text-sm">
                            {new Date(memory.timestamp).toLocaleDateString()}
                          </Text>
                          <Text type="secondary" className="text-xs">
                            {new Date(memory.timestamp).toLocaleTimeString()}
                          </Text>
                          {memory.score && (
                            <Badge
                              count={`${Math.round(memory.score * 100)}%`}
                              style={{
                                backgroundColor:
                                  memory.score > 0.7 ? "#52c41a" : "#faad14",
                              }}
                            />
                          )}
                        </div>

                        <Paragraph className="!mb-2 text-sm">
                          {memory.content}
                        </Paragraph>

                        {memory.piiDetected.length > 0 && (
                          <div className="mb-2">
                            <Text type="warning" className="text-xs mr-2">
                              <AlertTriangle className="h-3 w-3 inline mr-1" />
                              PII Detected:
                            </Text>
                            <Space size="small">
                              {memory.piiDetected.map((pii, index) => (
                                <Tag key={index} color="orange">
                                  {pii}
                                </Tag>
                              ))}
                            </Space>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col items-end gap-2 ml-4">
                        <Space size="small">
                          <Tooltip
                            title={
                              memory.isPrivate ? "Make Public" : "Make Private"
                            }
                          >
                            <Button
                              type="text"
                              size="small"
                              icon={
                                memory.isPrivate ? (
                                  <Lock className="h-4 w-4" />
                                ) : (
                                  <Unlock className="h-4 w-4" />
                                )
                              }
                              onClick={() => togglePrivacy(memory.id)}
                            />
                          </Tooltip>

                          {memory.piiDetected.length > 0 && (
                            <Tooltip title="Remove PII">
                              <Button
                                type="text"
                                size="small"
                                icon={<Shield className="h-4 w-4" />}
                                onClick={() => removePII(memory.id)}
                              />
                            </Tooltip>
                          )}

                          <Tooltip title="Delete Memory">
                            <Button
                              type="text"
                              size="small"
                              danger
                              icon={<Trash2 className="h-4 w-4" />}
                              onClick={() => deleteMemory(memory.id)}
                              loading={deleteMemoryMutation.isPending}
                            />
                          </Tooltip>
                        </Space>
                      </div>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
        </div>
      </Card>
    </div>
  );
};
