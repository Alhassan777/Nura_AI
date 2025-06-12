"use client";

import React, { useState } from "react";
import {
  Card,
  Switch,
  InputNumber,
  Button,
  Typography,
  Alert,
  Divider,
  Space,
  Input,
} from "antd";
import {
  Shield,
  AlertTriangle,
  Eye,
  Database,
  Clock,
  Search,
} from "lucide-react";
import {
  usePrivacySettings,
  useUpdatePrivacySettings,
  useAnalyzeText,
} from "@/services/hooks/use-privacy";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

export default function PrivacyPage() {
  const [analyzeText, setAnalyzeText] = useState("");
  const { data: settings, isLoading } = usePrivacySettings();
  const { mutate: updateSettings, isPending: isUpdating } =
    useUpdatePrivacySettings();
  const {
    mutate: analyzeTextMutation,
    isPending: isAnalyzing,
    data: analysisResult,
  } = useAnalyzeText();

  const handleSettingsUpdate = (key: string, value: any) => {
    updateSettings({ [key]: value });
  };

  const handleAnalyze = () => {
    if (analyzeText.trim()) {
      analyzeTextMutation(analyzeText);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">Loading privacy settings...</div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Shield className="h-8 w-8 text-blue-600" />
        <Title level={2} className="!mb-0">
          Privacy & Security Settings
        </Title>
      </div>

      {/* Privacy Detection Settings */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            <span>Personal Information Detection</span>
          </div>
        }
      >
        <Space direction="vertical" className="w-full" size="large">
          <div className="flex items-center justify-between">
            <div>
              <Text strong>Enable PII Detection</Text>
              <br />
              <Text type="secondary" className="text-sm">
                Automatically detect and flag personal information in
                conversations
              </Text>
            </div>
            <Switch
              checked={settings?.pii_detection_enabled}
              onChange={(checked) =>
                handleSettingsUpdate("pii_detection_enabled", checked)
              }
              loading={isUpdating}
            />
          </div>

          <Divider />

          <div className="flex items-center justify-between">
            <div>
              <Text strong>Data Retention Period</Text>
              <br />
              <Text type="secondary" className="text-sm">
                How long to keep personal data (in days)
              </Text>
            </div>
            <InputNumber
              min={1}
              max={365}
              value={settings?.data_retention_days}
              onChange={(value) =>
                handleSettingsUpdate("data_retention_days", value)
              }
              addonAfter="days"
              disabled={isUpdating}
            />
          </div>
        </Space>
      </Card>

      {/* Text Analysis Tool */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            <span>Privacy Analysis Tool</span>
          </div>
        }
      >
        <Space direction="vertical" className="w-full" size="large">
          <div>
            <Text strong>Analyze Text for Personal Information</Text>
            <Paragraph type="secondary">
              Test any text to see what personal information might be detected
            </Paragraph>
          </div>

          <TextArea
            rows={4}
            value={analyzeText}
            onChange={(e) => setAnalyzeText(e.target.value)}
            placeholder="Enter text to analyze for personal information..."
          />

          <Button
            type="primary"
            icon={<Search className="h-4 w-4" />}
            onClick={handleAnalyze}
            loading={isAnalyzing}
            disabled={!analyzeText.trim()}
          >
            Analyze Text
          </Button>

          {analysisResult && (
            <div className="bg-gray-50 p-4 rounded">
              <Title level={5}>Analysis Results</Title>
              {analysisResult.pii_detected?.length > 0 ? (
                <Space direction="vertical" className="w-full">
                  <Alert
                    message={`Found ${analysisResult.pii_detected.length} potential privacy concerns`}
                    type="warning"
                    icon={<AlertTriangle className="h-4 w-4" />}
                  />
                  {analysisResult.pii_detected.map(
                    (item: any, index: number) => (
                      <Card key={index} size="small" className="bg-white">
                        <div className="flex justify-between items-start">
                          <div>
                            <Text strong>{item.type}</Text>
                            <br />
                            <Text code>{item.text}</Text>
                            <br />
                            <Text type="secondary" className="text-sm">
                              {item.description}
                            </Text>
                          </div>
                          <div className="text-right">
                            <Text
                              strong
                              className={
                                item.risk_level === "high"
                                  ? "text-red-600"
                                  : item.risk_level === "medium"
                                  ? "text-orange-600"
                                  : "text-green-600"
                              }
                            >
                              {item.risk_level.toUpperCase()}
                            </Text>
                            <br />
                            <Text type="secondary" className="text-sm">
                              {Math.round(item.confidence * 100)}% confidence
                            </Text>
                          </div>
                        </div>
                      </Card>
                    )
                  )}
                </Space>
              ) : (
                <Alert
                  message="No personal information detected"
                  type="success"
                  icon={<Shield className="h-4 w-4" />}
                />
              )}
            </div>
          )}
        </Space>
      </Card>

      {/* Data Management */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            <span>Data Management</span>
          </div>
        }
      >
        <Space direction="vertical" className="w-full" size="large">
          <Alert
            message="Privacy by Design"
            description="Nura is built with privacy-first principles. Your conversations are processed locally when possible, and sensitive information is handled with the highest security standards."
            type="info"
            icon={<Shield className="h-4 w-4" />}
          />

          <div>
            <Title level={5}>Current Settings Summary</Title>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
              <li>
                PII Detection:{" "}
                {settings?.pii_detection_enabled ? "Enabled" : "Disabled"}
              </li>
              <li>
                Data Retention: {settings?.data_retention_days || 90} days
              </li>
              <li>Automatic Cleanup: Enabled</li>
              <li>Encryption: End-to-end for sensitive data</li>
            </ul>
          </div>
        </Space>
      </Card>
    </div>
  );
}
