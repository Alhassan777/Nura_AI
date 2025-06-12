"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button, Progress, Badge, Alert, Space, Tooltip } from "antd";
import { AudioOutlined, AudioMutedOutlined } from "@ant-design/icons";
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  MessageCircle,
} from "lucide-react";
import { useVapi, VapiMessage } from "@/hooks/useVapi";

interface VoiceChatProps {
  onEndCall?: () => void;
  onSwitchToChat?: () => void;
  assistantId?: string;
}

export const VoiceChat: React.FC<VoiceChatProps> = ({
  onEndCall,
  onSwitchToChat,
  assistantId,
}) => {
  const [transcript, setTranscript] = useState<string[]>([]);
  const [lastMessage, setLastMessage] = useState<string>("");

  // Initialize Vapi hook
  const { state, actions, utils } = useVapi({
    assistantId,
    onCallStart: () => {
      console.log("Voice call started");
    },
    onCallEnd: () => {
      console.log("Voice call ended");
      onEndCall?.();
    },
    onMessage: (message: VapiMessage) => {
      console.log("Received message:", message);

      // Handle transcript messages
      if (message.type === "transcript" && message.transcript) {
        const speaker = message.role === "user" ? "You" : "Nura";
        const transcriptLine = `${speaker}: ${message.transcript}`;
        setTranscript((prev) => [...prev.slice(-4), transcriptLine]); // Keep last 5 messages
        setLastMessage(transcriptLine);
      }
    },
    onError: (error: string) => {
      console.error("Voice error:", error);
    },
  });

  // Initialize Vapi connection when component mounts
  useEffect(() => {
    if (!utils.isInitialized) {
      actions.initializeVapi();
    }
  }, [utils.isInitialized, actions]);

  // Handle call start/stop
  const handleStartCall = async () => {
    if (!state.isConnected) return;
    await actions.startCall();
  };

  const handleEndCall = async () => {
    await actions.endCall();
  };

  // Handle mute toggle
  const handleToggleMute = () => {
    actions.toggleMute();
  };

  // Show error state
  if (state.error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6 text-center">
          <Alert
            type="error"
            message="Voice Connection Failed"
            description={state.error}
            showIcon
            className="mb-4"
          />
          <Space>
            <Button onClick={actions.initializeVapi}>Try Again</Button>
            <Button type="primary" onClick={onSwitchToChat}>
              Switch to Text Chat
            </Button>
          </Space>
        </CardContent>
      </Card>
    );
  }

  // Show loading state
  if (state.isLoading && !state.isConnected) {
    return (
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6 text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="text-blue-800">
              Initializing voice connection...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Call Status Header */}
      <Card
        className={
          state.isCallActive
            ? "border-green-200 bg-green-50"
            : "border-blue-200 bg-blue-50"
        }
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div
                className={`p-2 rounded-full ${
                  state.isCallActive ? "bg-green-100" : "bg-blue-100"
                }`}
              >
                <Phone
                  className={`h-5 w-5 ${
                    state.isCallActive ? "text-green-600" : "text-blue-600"
                  }`}
                />
              </div>
              <div>
                <h3
                  className={`font-semibold ${
                    state.isCallActive ? "text-green-800" : "text-blue-800"
                  }`}
                >
                  {state.isCallActive
                    ? "Voice call with Nura"
                    : "Ready to call Nura"}
                </h3>
                <p
                  className={`text-sm ${
                    state.isCallActive ? "text-green-600" : "text-blue-600"
                  }`}
                >
                  {state.isCallActive
                    ? `${utils.formatDuration(state.callDuration)} • Connected`
                    : state.isConnected
                    ? "Connected and ready"
                    : "Connecting..."}
                </p>
              </div>
            </div>

            <Badge
              status={
                state.isCallActive
                  ? "success"
                  : state.isConnected
                  ? "processing"
                  : "default"
              }
              text={
                state.isCallActive
                  ? "Active"
                  : state.isConnected
                  ? "Ready"
                  : "Connecting"
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Voice Visualization */}
      <Card>
        <CardContent className="p-8">
          <div className="text-center space-y-6">
            {/* Nura Avatar with speaking indicator */}
            <div className="relative mx-auto w-32 h-32">
              <div
                className={`w-32 h-32 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center ${
                  state.isAssistantSpeaking ? "animate-pulse" : ""
                }`}
              >
                <Volume2
                  className={`h-12 w-12 text-white ${
                    state.isAssistantSpeaking ? "animate-bounce" : ""
                  }`}
                />
              </div>

              {/* Speaking indicator rings */}
              {state.isAssistantSpeaking && (
                <>
                  <div className="absolute inset-0 rounded-full border-4 border-purple-300 animate-ping"></div>
                  <div className="absolute inset-2 rounded-full border-2 border-blue-300 animate-ping animation-delay-75"></div>
                </>
              )}
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-gray-900">
                {state.isAssistantSpeaking
                  ? "Nura is speaking..."
                  : state.isCallActive
                  ? "Say something..."
                  : "Ready to start conversation"}
              </h3>

              {/* Audio Level Indicator */}
              {state.isCallActive && (
                <div className="w-64 mx-auto">
                  <Progress
                    percent={state.audioLevel}
                    showInfo={false}
                    strokeColor={{
                      "0%": "#87CEEB",
                      "50%": "#4169E1",
                      "100%": "#FF1493",
                    }}
                    className="mb-2"
                  />
                  <p className="text-sm text-gray-500">
                    {state.audioLevel > 10 ? "Good signal" : "Speak louder"}
                  </p>
                </div>
              )}

              {/* Transcript Display */}
              {lastMessage && state.isCallActive && (
                <div className="bg-gray-100 p-3 rounded-lg max-w-md mx-auto">
                  <p className="text-sm text-gray-700">{lastMessage}</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Voice Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-6">
            {/* Mute Toggle */}
            <Tooltip title={state.isMuted ? "Unmute" : "Mute"}>
              <Button
                type={state.isMuted ? "primary" : "default"}
                danger={state.isMuted}
                shape="circle"
                size="large"
                icon={
                  state.isMuted ? (
                    <MicOff className="h-5 w-5" />
                  ) : (
                    <Mic className="h-5 w-5" />
                  )
                }
                onClick={handleToggleMute}
                className="w-16 h-16"
                disabled={!state.isCallActive}
              />
            </Tooltip>

            {/* Call Button */}
            <Tooltip title={state.isCallActive ? "End call" : "Start call"}>
              <Button
                type="primary"
                shape="circle"
                size="large"
                icon={
                  state.isCallActive ? (
                    <PhoneOff className="h-5 w-5" />
                  ) : (
                    <AudioOutlined />
                  )
                }
                onClick={state.isCallActive ? handleEndCall : handleStartCall}
                className={`w-20 h-20 text-lg ${
                  state.isCallActive
                    ? "bg-red-500 border-red-500 hover:bg-red-600"
                    : "bg-blue-500 border-blue-500 hover:bg-blue-600"
                }`}
                loading={state.isLoading}
                disabled={!state.isConnected}
              />
            </Tooltip>

            {/* Additional Controls */}
            <Tooltip title="Settings">
              <Button
                shape="circle"
                size="large"
                icon={<MessageCircle className="h-5 w-5" />}
                onClick={onSwitchToChat}
                className="w-16 h-16"
              />
            </Tooltip>
          </div>

          <div className="text-center mt-4">
            <Button type="text" size="small" onClick={onSwitchToChat}>
              Switch to Text Chat
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transcript History */}
      {transcript.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h4 className="font-semibold mb-3">Conversation</h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {transcript.map((line, index) => (
                <div
                  key={index}
                  className="text-sm text-gray-600 p-2 bg-gray-50 rounded"
                >
                  {line}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
