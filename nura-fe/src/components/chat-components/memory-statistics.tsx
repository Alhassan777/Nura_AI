import {
  Space,
  Card,
  Typography,
  Spin,
  Button,
  Badge,
  Empty,
  Col,
  Row,
} from "antd";

import { Clock, Database, RefreshCw, Trash2 } from "lucide-react";
import React from "react";
import MemoryItem from "./memory-item";
import { MemoryContext, MemoryStats } from "./types";

const { Text, Paragraph } = Typography;

export const MemoryStatistics = ({
  userId,
  isLoadingMemories,
  memoryStats,
  loadMemories,
  memoryContext,
}: {
  userId: string;
  isLoadingMemories: boolean;
  memoryStats: MemoryStats | null;
  loadMemories: () => void;
  memoryContext: MemoryContext | null;
}) => {
  const clearMemories = async () => {
    if (
      !confirm(
        "Are you sure you want to clear all memories? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: `/memory/forget?user_id=${userId}`,
          method: "POST",
        }),
      });

      if (response.ok) {
        // await loadMemories();
      } else {
        console.error("Failed to clear memories");
      }
    } catch (error) {
      console.error("Error clearing memories:", error);
    }
  };

  return (
    <div className="w-full h-full flex flex-wrap gap-4">
      <div className="w-full">
        <Card
          title={
            <Space>
              <Database />
              Memory Statistics
            </Space>
          }
        >
          {isLoadingMemories ? (
            <Spin tip="Loading statistics..." />
          ) : memoryStats && memoryStats.total > 0 ? (
            <Space direction="vertical" style={{ width: "100%" }}>
              <Row justify="space-between">
                <Col>
                  <Text>Total Memories:</Text>
                </Col>
                <Col>
                  <Text strong>{memoryStats.total}</Text>
                </Col>
              </Row>
              <Row justify="space-between">
                <Col>
                  <Text>Short-term:</Text>
                </Col>
                <Col>
                  <Text strong>{memoryStats.short_term}</Text>
                </Col>
              </Row>
              <Row justify="space-between">
                <Col>
                  <Text>Long-term:</Text>
                </Col>
                <Col>
                  <Text strong>{memoryStats.long_term}</Text>
                </Col>
              </Row>
              <Row justify="space-between">
                <Col>
                  <Text>Sensitive:</Text>
                </Col>
                <Col>
                  <Text strong type="danger">
                    {memoryStats.sensitive}
                  </Text>
                </Col>
              </Row>
            </Space>
          ) : (
            <Text type="secondary">No statistics available</Text>
          )}
          <Space style={{ marginTop: "16px", width: "100%" }}>
            <Button
              onClick={loadMemories}
              icon={<RefreshCw className="h-4 w-4" />}
              disabled={isLoadingMemories}
              style={{ flex: 1 }}
            >
              Refresh
            </Button>
            <Button
              onClick={clearMemories}
              danger
              icon={<Trash2 className="h-4 w-4" />}
              disabled={isLoadingMemories}
              style={{ flex: 1 }}
            >
              Clear All
            </Button>
          </Space>
        </Card>
      </div>
      <div className="w-full">
        <div className="flex flex-col gap-4">
          <Card title="📋 Session Notes">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800 mb-2">
                <strong>Short-term memories are session-based</strong>
              </p>
              <p className="text-xs text-blue-600">
                These memories exist only during your current chat session and
                are automatically cleared when the conversation ends. Important
                information gets promoted to long-term memory for future
                reference.
              </p>
            </div>
          </Card>
          <Card
            title={
              <Space>
                <Database />
                Long-term Memories{" "}
                {memoryContext?.long_term && (
                  <Badge
                    count={memoryContext.long_term.length}
                    style={{
                      backgroundColor: "#f6ffed",
                      color: "#52c41a",
                    }}
                  />
                )}
              </Space>
            }
          >
            {isLoadingMemories ? (
              <Spin tip="Loading long-term memories..." />
            ) : memoryContext?.long_term &&
              memoryContext.long_term.length > 0 ? (
              <div
                style={{
                  maxHeight: "400px",
                  overflowY: "auto",
                  paddingRight: "8px",
                }}
              >
                {memoryContext.long_term.map((memory) => (
                  <MemoryItem
                    key={memory.id || `long-term-${memory.timestamp}`}
                    memory={memory}
                    typeLabel="Long-term"
                  />
                ))}
              </div>
            ) : (
              <Empty
                description="No long-term memories found. Memories with high stability scores will appear here."
                image={
                  <Database style={{ fontSize: "48px", color: "#bfbfbf" }} />
                }
              />
            )}
          </Card>
          {memoryContext?.digest && (
            <Card title="Memory Digest">
              <Paragraph type="secondary">{memoryContext.digest}</Paragraph>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoryStatistics;
