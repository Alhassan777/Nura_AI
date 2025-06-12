import {
  Col,
  Row,
  Space,
  Card,
  Typography,
  Spin,
  Button,
  Badge,
  Empty,
} from "antd";
import { Database, RefreshCw, Heart } from "lucide-react";
import React from "react";
import { formatTimestamp } from "./utils";
import { MemoryContext } from "./types";

const { Text, Paragraph } = Typography;

export const EmotionalAnchors = ({
  isLoadingMemories,
  memoryContext,
  loadMemories,
}: {
  isLoadingMemories: boolean;
  memoryContext: MemoryContext | null;
  loadMemories: () => void;
}) => {
  return (
    <div className="w-full h-full flex flex-wrap gap-4">
      <div className="w-full flex-1">
        <Card
          title={
            <Space>
              <Heart />
              Emotional Anchors Info
            </Space>
          }
          style={{ marginBottom: "24px" }}
        >
          {isLoadingMemories ? (
            <Spin tip="Loading anchors..." />
          ) : memoryContext?.emotional_anchors &&
            memoryContext.emotional_anchors.length > 0 ? (
            <Space direction="vertical" style={{ width: "100%" }}>
              <Row justify="space-between">
                <Col>
                  <Text>Total Anchors:</Text>
                </Col>
                <Col>
                  <Text strong>{memoryContext.emotional_anchors.length}</Text>
                </Col>
              </Row>
              <Paragraph type="secondary" style={{ fontSize: "12px" }}>
                Meaningful connections that serve as emotional touchstones and
                coping resources. These are symbolic, lasting memories that
                provide stability.
              </Paragraph>
            </Space>
          ) : (
            <Text type="secondary">No anchors data available.</Text>
          )}
          <Button
            onClick={loadMemories}
            icon={<RefreshCw className="h-4 w-4" />}
            disabled={isLoadingMemories}
            style={{ marginTop: "16px" }}
            block
          >
            Refresh
          </Button>
        </Card>
        <Card title="Anchor Categories">
          <Paragraph style={{ fontSize: "12px" }} type="secondary">
            🏛️ <strong>Beliefs:</strong> Core values & philosophies
            <br />⚓ <strong>Places:</strong> Locations of safety & comfort
            <br />
            🎨 <strong>Creative:</strong> Artistic expressions
            <br />
            🔮 <strong>Symbolic:</strong> Meaningful symbols & metaphors
            <br />
            💎 <strong>Objects:</strong> Treasured items with deep meaning
            <br />
            👥 <strong>Relationships:</strong> Meaningful connections
            <br />✨ <strong>Experiences:</strong> Transformative moments
          </Paragraph>
        </Card>
      </div>
      <div className="w-full flex-1">
        <Card
          title={
            <Space>
              <Heart />
              Your Emotional Anchors{" "}
              {memoryContext?.emotional_anchors && (
                <Badge
                  count={memoryContext.emotional_anchors.length}
                  style={{
                    backgroundColor: "#fff0f6",
                    color: "#c41d7f",
                  }}
                />
              )}
            </Space>
          }
        >
          {isLoadingMemories ? (
            <Spin tip="Loading emotional anchors..." />
          ) : memoryContext?.emotional_anchors &&
            memoryContext.emotional_anchors.length > 0 ? (
            <div
              style={{
                maxHeight: "600px",
                overflowY: "auto",
                paddingRight: "8px",
              }}
            >
              {memoryContext.emotional_anchors.map((anchor) => (
                <Card
                  key={anchor.id}
                  size="small"
                  style={{
                    marginBottom: "12px",
                    background: "linear-gradient(to right, #fff0f6, #f9f0ff)",
                    borderColor: "#ffadd2",
                  }}
                >
                  <Paragraph strong>{anchor.content}</Paragraph>
                  <Space
                    wrap
                    size="small"
                    style={{
                      marginTop: "8px",
                      marginBottom: "8px",
                    }}
                  >
                    <Badge
                      count="emotional anchor"
                      style={{
                        backgroundColor: "#fff0f6",
                        color: "#c41d7f",
                        borderColor: "#ffadd2",
                      }}
                    />

                    {/* Show simplified classification */}
                    {anchor.metadata?.is_meaningful && (
                      <Badge
                        count="meaningful"
                        style={{
                          backgroundColor: "#f6ffed",
                          color: "#52c41a",
                          borderColor: "#b7eb8f",
                        }}
                      />
                    )}

                    {anchor.metadata?.is_lasting && (
                      <Badge
                        count="lasting"
                        style={{
                          backgroundColor: "#e6fffb",
                          color: "#13c2c2",
                          borderColor: "#87e8de",
                        }}
                      />
                    )}

                    {anchor.metadata?.is_symbolic && (
                      <Badge
                        count="symbolic"
                        style={{
                          backgroundColor: "#f9f0ff",
                          color: "#722ed1",
                          borderColor: "#d3adf7",
                        }}
                      />
                    )}

                    <Badge
                      count={anchor.type}
                      style={{
                        backgroundColor: "#fff1b8",
                        color: "#fa8c16",
                      }}
                    />

                    {anchor.metadata?.has_pii && (
                      <Badge status="error" text="Contains PII" />
                    )}
                  </Space>
                  <div style={{ fontSize: "12px", color: "gray" }}>
                    <Text type="secondary">
                      Created: {formatTimestamp(anchor.timestamp)}
                    </Text>
                    {anchor.metadata?.relevance_score && (
                      <Text type="secondary" style={{ marginLeft: "12px" }}>
                        Relevance:{" "}
                        {(anchor.metadata.relevance_score * 100).toFixed(0)}%
                      </Text>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Empty
              description="No emotional anchors found. Memories with symbolic meaning and lasting significance will appear here."
              image={<Heart style={{ fontSize: "48px", color: "#bfbfbf" }} />}
            />
          )}
        </Card>
      </div>
    </div>
  );
};

export default EmotionalAnchors;
