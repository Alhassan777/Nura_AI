import { Space, Card, Typography, Badge } from "antd";
import React from "react";
import { MemoryItem as MemoryItemType } from "./types";
import { formatTimestamp } from "./utils";

const MemoryItem = ({
  memory,
  typeLabel,
}: {
  memory: MemoryItemType;
  typeLabel: string;
}) => {
  const { Text, Paragraph } = Typography;

  // Compute is_emotional_anchor from memory_category
  const isEmotionalAnchor =
    memory.metadata?.memory_category === "emotional_anchor" ||
    memory.is_emotional_anchor;

  return (
    <Card key={memory.id} size="small" style={{ marginBottom: "12px" }}>
      <Paragraph ellipsis={{ rows: 3, expandable: true, symbol: "more" }}>
        {memory.content}
      </Paragraph>
      <Space wrap size="small" style={{ marginTop: "8px" }}>
        <Badge
          style={{
            backgroundColor: "#e6f7ff",
            color: "#1890ff",
            borderColor: "#91d5ff",
          }}
          count={typeLabel}
        />
        <Badge
          style={{
            backgroundColor: "#f6ffed",
            color: "#52c41a",
            borderColor: "#b7eb8f",
          }}
          count={memory.type}
        />

        {/* Show simplified classification */}
        {memory.metadata?.memory_category && (
          <Badge
            style={{
              backgroundColor:
                memory.metadata.memory_category === "emotional_anchor"
                  ? "#fff0f6"
                  : memory.metadata.memory_category === "long_term"
                  ? "#f9f0ff"
                  : "#e6f7ff",
              color:
                memory.metadata.memory_category === "emotional_anchor"
                  ? "#c41d7f"
                  : memory.metadata.memory_category === "long_term"
                  ? "#722ed1"
                  : "#1890ff",
              borderColor:
                memory.metadata.memory_category === "emotional_anchor"
                  ? "#ffadd2"
                  : memory.metadata.memory_category === "long_term"
                  ? "#d3adf7"
                  : "#91d5ff",
            }}
            count={memory.metadata.memory_category.replace("_", " ")}
          />
        )}

        {/* Show boolean flags */}
        {memory.metadata?.is_meaningful && (
          <Badge
            style={{
              backgroundColor: "#f6ffed",
              color: "#52c41a",
              borderColor: "#b7eb8f",
            }}
            count="meaningful"
          />
        )}

        {memory.metadata?.is_lasting && (
          <Badge
            style={{
              backgroundColor: "#e6fffb",
              color: "#13c2c2",
              borderColor: "#87e8de",
            }}
            count="lasting"
          />
        )}

        {memory.metadata?.is_symbolic && (
          <Badge
            style={{
              backgroundColor: "#f9f0ff",
              color: "#722ed1",
              borderColor: "#d3adf7",
            }}
            count="symbolic"
          />
        )}

        {isEmotionalAnchor && (
          <Badge status="success" text="Emotional Anchor" />
        )}

        {memory.metadata?.has_pii && (
          <Badge status="error" text="Contains PII" />
        )}
      </Space>
      <div style={{ fontSize: "12px", color: "gray", marginTop: "8px" }}>
        <Text type="secondary">
          Created: {formatTimestamp(memory.timestamp)}
        </Text>
        {memory.metadata?.score &&
          (memory.metadata.score.relevance !== undefined ||
            memory.metadata.score.stability !== undefined ||
            memory.metadata.score.explicitness !== undefined) && (
            <Space size="middle" style={{ marginTop: "4px" }}>
              <Text type="secondary">
                Relevance:{" "}
                {memory.metadata.score.relevance?.toFixed(2) || "N/A"}
              </Text>
              <Text type="secondary">
                Stability:{" "}
                {memory.metadata.score.stability?.toFixed(2) || "N/A"}
              </Text>
              <Text type="secondary">
                Explicitness:{" "}
                {memory.metadata.score.explicitness?.toFixed(2) || "N/A"}
              </Text>
            </Space>
          )}
        {memory.metadata?.detected_items &&
          Array.isArray(memory.metadata.detected_items) &&
          memory.metadata.detected_items.length > 0 && (
            <div style={{ marginTop: "4px" }}>
              <Text type="secondary">
                PII Types: {memory.metadata.detected_items.join(", ")}
              </Text>
            </div>
          )}
        <details style={{ marginTop: "8px" }}>
          <summary
            style={{ cursor: "pointer", fontSize: "12px", color: "#1890ff" }}
          >
            🔍 Debug: Raw Memory Data
          </summary>
          <pre
            style={{
              marginTop: "4px",
              padding: "8px",
              backgroundColor: "#f5f5f5",
              borderRadius: "4px",
              fontSize: "12px",
              maxHeight: "100px",
              overflow: "auto",
            }}
          >
            {JSON.stringify(memory, null, 2)}
          </pre>
        </details>
      </div>
    </Card>
  );
};

export default MemoryItem;
