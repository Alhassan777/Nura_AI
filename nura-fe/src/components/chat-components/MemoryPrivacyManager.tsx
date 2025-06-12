"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  Button,
  Badge,
  Alert as AntdAlert,
  Spin,
  Space,
  Typography,
  message,
} from "antd";
import { Shield, AlertTriangle, Eye, EyeOff } from "lucide-react";
import { MemoryWithPII, PrivacyReviewData } from "./types";
import {
  getChoiceButtonType,
  getChoiceIcon,
  getRiskBadgeStatus,
  getStorageIcon,
} from "./utils";
import { useApplyPrivacyChoices, useGetPrivacyReview } from "@/services/hooks";

const {
  Title: AntdTitle,
  Text: AntdText,
  Paragraph: AntdParagraph,
} = Typography;

const MemoryPrivacyManager: React.FC<{ userId: string }> = ({ userId }) => {
  const [privacyData, setPrivacyData] = useState<PrivacyReviewData | null>(
    null
  );
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [showPIIDetails, setShowPIIDetails] = useState<Record<string, boolean>>(
    {}
  );
  const [results, setResults] = useState<any>(null);

  const {
    data: privacyReview,
    isLoading: isLoadingPrivacyReview,
    refetch: refetchPrivacyReview,
  } = useGetPrivacyReview(userId);
  const {
    mutateAsync: applyPrivacyChoicesMutation,
    isPending: isApplyingPrivacyChoices,
  } = useApplyPrivacyChoices();

  useEffect(() => {
    if (privacyReview) {
      setPrivacyData(privacyReview);
      const initialChoices: Record<string, string> = {};
      privacyReview.memories_with_pii.forEach((memory: MemoryWithPII) => {
        initialChoices[memory.id] = "keep_original";
      });
      setChoices(initialChoices);
    }
  }, [privacyReview]);

  const handleChoiceChange = (memoryId: string, choice: string) => {
    setChoices((prev) => ({
      ...prev,
      [memoryId]: choice,
    }));
  };

  const togglePIIDetails = (memoryId: string) => {
    setShowPIIDetails((prev) => ({
      ...prev,
      [memoryId]: !prev[memoryId],
    }));
  };

  if (isLoadingPrivacyReview) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "32px",
        }}
      >
        <Spin size="large" />
        <span style={{ marginLeft: "8px" }}>Loading privacy review...</span>
      </div>
    );
  }

  if (!privacyData || privacyData.total_count === 0) {
    return (
      <Card>
        <AntdAlert
          message="Privacy Review"
          description="No memories with sensitive information found. Your privacy is protected!"
          type="success"
          showIcon
          icon={<Shield className="w-5 h-5" />}
        />
      </Card>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Space align="center">
          <Shield className="w-5 h-5 text-blue-600" />
          <AntdTitle level={4} style={{ margin: 0 }}>
            Memory Privacy Manager
          </AntdTitle>
        </Space>
        <AntdParagraph type="secondary">
          Review and manage {privacyData.total_count} memories containing
          sensitive information
        </AntdParagraph>
      </Card>

      {results && (
        <AntdAlert
          message="Privacy choices applied successfully!"
          description={`Removed: ${results.summary.removed_entirely}, PII Cleaned: ${results.summary.pii_removed}, Kept Original: ${results.summary.kept_original}`}
          type="success"
          showIcon
          closable
          onClose={() => setResults(null)}
        />
      )}

      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        {privacyData.memories_with_pii.map((memory) => (
          <Card
            key={memory.id}
            bordered={false}
            style={{ borderLeft: "4px solid orange" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div style={{ flex: 1 }}>
                <Space align="center" style={{ marginBottom: "8px" }}>
                  {getStorageIcon(
                    memory.storage_type,
                    memory.is_emotional_anchor
                  )}
                  <AntdText strong>
                    {memory.is_emotional_anchor
                      ? "Emotional Anchor"
                      : memory.storage_type === "short_term"
                      ? "Short-term Memory"
                      : "Long-term Memory"}
                  </AntdText>
                  <Badge
                    count={memory.memory_type}
                    style={{ backgroundColor: "#f0f0f0", color: "#595959" }}
                  />
                </Space>

                <AntdParagraph style={{ marginBottom: "12px" }}>
                  {memory.content}
                </AntdParagraph>

                <Space align="center" wrap style={{ marginBottom: "12px" }}>
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  <AntdText strong>Sensitive Information Detected:</AntdText>
                  {memory.pii_summary.high_risk_count > 0 && (
                    <Badge
                      status={getRiskBadgeStatus("high")}
                      text={`${memory.pii_summary.high_risk_count} High Risk`}
                    />
                  )}
                  {memory.pii_summary.medium_risk_count > 0 && (
                    <Badge
                      status={getRiskBadgeStatus("medium")}
                      text={`${memory.pii_summary.medium_risk_count} Medium Risk`}
                    />
                  )}
                  {memory.pii_summary.low_risk_count > 0 && (
                    <Badge
                      status={getRiskBadgeStatus("low")}
                      text={`${memory.pii_summary.low_risk_count} Low Risk`}
                    />
                  )}
                  <Button
                    type="text"
                    size="small"
                    onClick={() => togglePIIDetails(memory.id)}
                    icon={
                      showPIIDetails[memory.id] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )
                    }
                    style={{ marginLeft: "auto" }}
                  >
                    {showPIIDetails[memory.id]
                      ? "Hide Details"
                      : "Show Details"}
                  </Button>
                </Space>

                {showPIIDetails[memory.id] && (
                  <div
                    style={{
                      backgroundColor: "#fafafa",
                      padding: "12px",
                      borderRadius: "4px",
                      marginBottom: "12px",
                    }}
                  >
                    <AntdTitle level={5} style={{ marginBottom: "8px" }}>
                      Detected Sensitive Information:
                    </AntdTitle>
                    <Space direction="vertical" style={{ width: "100%" }}>
                      {memory.pii_detected.map((pii, index) => (
                        <div
                          key={index}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            fontSize: "14px",
                          }}
                        >
                          <AntdText code>{pii.text}</AntdText>
                          <Space>
                            <Badge
                              status={getRiskBadgeStatus(pii.risk_level)}
                              text={pii.type}
                            />
                            <AntdText type="secondary">
                              {Math.round(pii.confidence * 100)}% confidence
                            </AntdText>
                          </Space>
                        </div>
                      ))}
                    </Space>
                  </div>
                )}
              </div>
            </div>
            <div>
              <AntdTitle
                level={5}
                style={{ marginBottom: "12px", marginTop: "10px" }}
              >
                Choose how to handle this memory:
              </AntdTitle>
              <Space wrap style={{ width: "100%" }}>
                {Object.entries(privacyData.privacy_options).map(
                  ([key, option]) => (
                    <Button
                      key={key}
                      onClick={() => handleChoiceChange(memory.id, key)}
                      icon={getChoiceIcon(key)}
                      type={getChoiceButtonType(choices[memory.id], key)}
                      danger={
                        key === "remove_entirely" && choices[memory.id] === key
                      }
                      style={{ flex: "1 0 30%", minWidth: "150px" }}
                    >
                      <Space direction="vertical" align="start" size={0}>
                        <AntdText strong>{option.label}</AntdText>
                        <AntdText type="secondary" style={{ fontSize: "12px" }}>
                          {option.description}
                        </AntdText>
                      </Space>
                    </Button>
                  )
                )}
              </Space>
            </div>
          </Card>
        ))}
      </Space>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          paddingTop: "16px",
        }}
      >
        <Button
          type="primary"
          onClick={async () => {
            try {
              await applyPrivacyChoicesMutation({ userId, choices });
              await refetchPrivacyReview();
              message.success("Privacy choices applied successfully");
            } catch (error) {
              console.error("Error applying privacy choices:", error);
              message.error("Error applying privacy choices");
            }
          }}
          loading={isApplyingPrivacyChoices}
          icon={<Shield className="w-4 h-4" />}
          size="large"
        >
          {isApplyingPrivacyChoices
            ? "Applying Choices..."
            : "Apply Privacy Choices"}
        </Button>
      </div>
    </Space>
  );
};

export default MemoryPrivacyManager;
