"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Radio, Space, Badge, Tooltip } from "antd";
import {
  MessageOutlined,
  PhoneOutlined,
  SoundOutlined,
} from "@ant-design/icons";
import { MessageCircle, Phone, Mic, Settings, Volume2 } from "lucide-react";

export type CommunicationMode = "chat" | "voice";

interface CommunicationModeSelectorProps {
  currentMode: CommunicationMode;
  onModeChange: (mode: CommunicationMode) => void;
  onStartConversation: () => void;
  isConnected?: boolean;
  isActive?: boolean;
}

export const CommunicationModeSelector: React.FC<
  CommunicationModeSelectorProps
> = ({
  currentMode,
  onModeChange,
  onStartConversation,
  isConnected = false,
  isActive = false,
}) => {
  const [showSettings, setShowSettings] = useState(false);

  const modes = [
    {
      key: "chat" as CommunicationMode,
      title: "Text Chat",
      description: "Type your thoughts and feelings",
      icon: <MessageCircle className="h-8 w-8" />,
      antIcon: <MessageOutlined />,
      benefits: [
        "Take your time to express yourself",
        "Easy to reference previous conversations",
        "Clear and private communication",
        "Available 24/7",
      ],
      color: "blue",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
    },
    {
      key: "voice" as CommunicationMode,
      title: "Voice Call",
      description: "Speak naturally with Nura",
      icon: <Phone className="h-8 w-8" />,
      antIcon: <PhoneOutlined />,
      benefits: [
        "Natural, conversational interaction",
        "Express emotions through tone",
        "Hands-free communication",
        "Immediate, real-time responses",
      ],
      color: "green",
      bgColor: "bg-green-50",
      borderColor: "border-green-200",
    },
  ];

  const selectedMode = modes.find((mode) => mode.key === currentMode);

  return (
    <div className="space-y-6">
      {/* Mode Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modes.map((mode) => {
          const isSelected = currentMode === mode.key;

          return (
            <Card
              key={mode.key}
              className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                isSelected
                  ? `ring-2 ring-${mode.color}-500 ${mode.bgColor} ${mode.borderColor}`
                  : "hover:border-gray-300"
              }`}
              onClick={() => onModeChange(mode.key)}
            >
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div
                    className={`p-3 rounded-full ${
                      isSelected ? `bg-${mode.color}-100` : "bg-gray-100"
                    }`}
                  >
                    <div
                      className={
                        isSelected ? `text-${mode.color}-600` : "text-gray-600"
                      }
                    >
                      {mode.icon}
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {mode.title}
                      </h3>
                      {isSelected && (
                        <Radio checked className="pointer-events-none" />
                      )}
                    </div>

                    <p className="text-gray-600 text-sm mb-3">
                      {mode.description}
                    </p>

                    <ul className="space-y-1">
                      {mode.benefits.map((benefit, index) => (
                        <li
                          key={index}
                          className="text-xs text-gray-500 flex items-center"
                        >
                          <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                          {benefit}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Action Section */}
      <Card
        className={
          selectedMode
            ? `border-${selectedMode.color}-200 ${selectedMode.bgColor}`
            : ""
        }
      >
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <div className="flex items-center justify-center space-x-2">
              {selectedMode?.antIcon}
              <h3 className="text-xl font-semibold text-gray-900">
                Ready to connect via {selectedMode?.title}
              </h3>
            </div>

            <p className="text-gray-600">
              {currentMode === "chat"
                ? "Start typing to begin your conversation with Nura"
                : "Click to start a voice conversation with Nura"}
            </p>

            <div className="flex items-center justify-center space-x-3">
              <Button
                type="primary"
                size="large"
                icon={selectedMode?.antIcon}
                onClick={onStartConversation}
                className={`px-8 py-3 h-auto text-base font-medium`}
                loading={isActive}
              >
                {isActive ? `Connecting...` : `Start ${selectedMode?.title}`}
              </Button>
            </div>

            {/* Connection Status */}
            {currentMode === "voice" && (
              <div className="flex items-center justify-center space-x-2 text-sm">
                <Badge
                  status={isConnected ? "success" : "default"}
                  text={
                    isConnected ? "Voice system ready" : "Voice system offline"
                  }
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Switch */}
      <div className="text-center">
        <Button
          type="text"
          size="small"
          onClick={() =>
            onModeChange(currentMode === "chat" ? "voice" : "chat")
          }
          className="text-gray-500 hover:text-gray-700"
        >
          Switch to {currentMode === "chat" ? "Voice Call" : "Text Chat"}
        </Button>
      </div>
    </div>
  );
};
