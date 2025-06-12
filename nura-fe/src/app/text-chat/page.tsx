"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Typography, Tabs, Space } from "antd";
import {
  MessageCircle,
  Phone,
  ArrowLeft,
  Shield,
  Eye,
  EyeOff,
  Brain,
  Heart,
  Target,
} from "lucide-react";
import { Chat } from "@/components/chat-components/chat";
import { MemoryManagement } from "@/components/memory/MemoryManagement";
import { useRouter } from "next/navigation";

const { Title, Paragraph } = Typography;

export default function TextChatPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("chat");

  const tabItems = [
    {
      key: "chat",
      label: (
        <Space>
          <MessageCircle className="h-4 w-4" />
          Chat
        </Space>
      ),
      children: <Chat mode="production" />,
    },
    {
      key: "short-term",
      label: (
        <Space>
          <Brain className="h-4 w-4" />
          Short-term Memory
        </Space>
      ),
      children: <MemoryManagement memoryType="short-term" />,
    },
    {
      key: "long-term",
      label: (
        <Space>
          <Target className="h-4 w-4" />
          Long-term Memory
        </Space>
      ),
      children: <MemoryManagement memoryType="long-term" />,
    },
    {
      key: "anchors",
      label: (
        <Space>
          <Heart className="h-4 w-4" />
          Emotional Anchors
        </Space>
      ),
      children: <MemoryManagement memoryType="anchors" />,
    },
  ];

  return (
    <div className="container mx-auto p-4 h-screen flex flex-col">
      {/* Header */}
      <Card className="mb-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                type="text"
                icon={<ArrowLeft className="h-4 w-4" />}
                onClick={() => router.back()}
              >
                Back
              </Button>
              <MessageCircle className="h-6 w-6 text-blue-600" />
              <div>
                <CardTitle className="!mb-1">Chat with Nura</CardTitle>
                <Paragraph className="text-sm text-gray-600 !mb-0 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  Private conversation with memory management
                </Paragraph>
              </div>
            </div>
            <Button
              type="default"
              icon={<Phone className="h-4 w-4" />}
              onClick={() => router.push("/voice-chat")}
            >
              Switch to Voice
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Tabbed Interface */}
      <div className="flex-1 overflow-hidden">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          className="h-full"
          tabBarStyle={{
            marginBottom: 16,
            paddingLeft: 16,
            paddingRight: 16,
          }}
          tabBarExtraContent={
            <Space>
              <Typography.Text type="secondary" className="text-xs">
                <Shield className="h-3 w-3 inline mr-1" />
                PII Detection Active
              </Typography.Text>
            </Space>
          }
        />
      </div>
    </div>
  );
}
