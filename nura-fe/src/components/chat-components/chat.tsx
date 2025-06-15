"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Card,
  Empty,
  Spin,
  Badge,
  Typography,
  Alert as AntdAlert,
  Button,
  Input,
  Modal,
  Divider,
  Space,
  Tag,
  List,
  Tooltip,
  message as antMessage,
} from "antd";
import {
  Bot,
  Loader2,
  Send,
  User,
  AlertTriangle,
  Phone,
  MessageCircle,
  Calendar,
  Target,
  CheckCircle,
  Clock,
  Mic,
  MicOff,
  Brain,
  Heart,
  TrendingUp,
  ExternalLink,
} from "lucide-react";
import { ChatMessage } from "./types";
import { getCrisisLevelBadgeStatus } from "./utils";
import { useSendMessage } from "@/services/hooks";
import {
  CommunicationModeSelector,
  CommunicationMode,
} from "../CommunicationModeSelector";
import { VoiceChat } from "../voice/VoiceChat";
import { useQueryClient } from "@tanstack/react-query";
import { axiosInstance } from "@/services/apis";
import { useRouter } from "next/navigation";

const { Text, Paragraph } = Typography;

interface ChatProps {
  // Configuration props
  mode?: "development" | "production";
  showTestScenarios?: boolean;
  showVoiceToggle?: boolean;
  enableTabInterface?: boolean;
  chatMode?: "general" | "action_plan" | "visualization";

  // Legacy props for backward compatibility
  activeTab?: string;
  loadMemories?: () => void;
  conversationId?: string;
}

export const Chat = ({
  mode = "production",
  showTestScenarios = false,
  showVoiceToggle = false,
  enableTabInterface = false,
  chatMode = "general",
  activeTab,
  loadMemories,
  conversationId,
}: ChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [communicationMode, setCommunicationMode] =
    useState<CommunicationMode>("chat");
  const [showCrisisModal, setShowCrisisModal] = useState(false);
  const [currentCrisisData, setCurrentCrisisData] = useState<any>(null);
  const [showActionPlanModal, setShowActionPlanModal] = useState(false);
  const [currentActionPlan, setCurrentActionPlan] = useState<any>(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [currentScheduleSuggestion, setCurrentScheduleSuggestion] =
    useState<any>(null);
  const [isCreatingActionPlan, setIsCreatingActionPlan] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const router = useRouter();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const { mutateAsync: sendMessage, isPending: isSending } = useSendMessage();

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    const messageText = inputValue;
    const messageId = Date.now().toString();
    setInputValue("");

    // For production mode, show user message immediately with loading state
    if (mode === "production") {
      const userMessage: ChatMessage = {
        id: messageId,
        message: messageText,
        response: "",
        crisis_level: "SUPPORT",
        crisis_explanation: "",
        resources_provided: [],
        coping_strategies: [],
        memory_stored: false,
        timestamp: new Date().toISOString(),
        configuration_warning: false,
        isUserMessage: true,
      };
      setMessages((prev) => [...prev, userMessage]);
    }

    try {
      const response = await sendMessage({
        message: messageText,
        include_memory: true,
        conversation_id: conversationId,
        chat_mode: chatMode,
      });

      // Handle multi-modal response format
      if (response.background_task_id) {
        // This is a multi-modal response - get background results with retry logic
        const pollBackgroundResults = async (
          taskId: string,
          maxRetries = 8,
          delay = 500
        ) => {
          for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
              console.log(
                `Polling background results (attempt ${attempt}/${maxRetries}) for task: ${taskId}`
              );

              const backgroundResponse = await axiosInstance.get(
                `/chat-v2/background-results/${taskId}`
              );

              console.log(
                "Background results received:",
                backgroundResponse.data
              );
              const backgroundData = backgroundResponse.data;

              // Check processing status
              if (backgroundData.status === "processing") {
                console.log("Background processing still running, waiting...");
                if (attempt < maxRetries) {
                  await new Promise((resolve) => setTimeout(resolve, delay));
                  delay = Math.min(delay * 1.2, 3000); // Gradual increase
                  continue;
                } else {
                  console.warn(
                    "Background processing taking longer than expected"
                  );
                  return; // Exit gracefully without throwing
                }
              }

              if (backgroundData.status === "error") {
                console.error(
                  "Background processing failed:",
                  backgroundData.error
                );
                return; // Exit gracefully
              }

              // Processing completed successfully
              const modeSpecific = backgroundData.tasks?.mode_specific;

              // Check for action plan suggestions
              if (modeSpecific?.should_suggest_action_plan) {
                console.log("Action plan suggestion found:", modeSpecific);
                setCurrentActionPlan({
                  ...modeSpecific,
                  background_task_id: taskId,
                  action_plan_type:
                    modeSpecific.action_plan?.plan_type || "hybrid",
                  extracted_action_plan: modeSpecific.action_plan || {},
                });
                setShowActionPlanModal(true);
              }

              // Check for crisis intervention
              const crisisData = backgroundData.tasks?.crisis_assessment;
              if (crisisData?.crisis_flag && crisisData?.level === "CRISIS") {
                setCurrentCrisisData(crisisData);
                setShowCrisisModal(true);
              }

              // Check for schedule suggestions
              const scheduleData =
                backgroundData.tasks?.mode_specific?.schedule_suggestion;
              if (scheduleData?.should_suggest_scheduling) {
                setCurrentScheduleSuggestion(scheduleData);
                setShowScheduleModal(true);
              }

              // Success - exit retry loop
              break;
            } catch (error: any) {
              console.log(
                `Background results polling attempt ${attempt} failed:`,
                error.response?.status,
                error.message
              );

              // With the new status system, 404s should be rare and indicate a real problem
              if (error.response?.status === 404) {
                console.error(
                  "Background task not found - task may have expired or failed to initialize"
                );
                break; // Don't retry 404s with the new system
              } else {
                console.error("Error polling background results:", error);
                // Retry other errors briefly
                if (attempt < 3) {
                  await new Promise((resolve) => setTimeout(resolve, 1000));
                  continue;
                }
                break;
              }
            }
          }
        };

        // Start polling immediately since we now cache pending status
        pollBackgroundResults(response.background_task_id);
      }

      if (mode === "production") {
        // Update the existing message with bot response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? {
                  ...msg,
                  response: response.response,
                  crisis_level: response.immediate_flags?.crisis_detected
                    ? "CRISIS"
                    : "SUPPORT",
                  crisis_explanation: response.immediate_flags?.crisis_detected
                    ? "Crisis detected"
                    : "",
                  resources_provided: response.immediate_flags?.needs_resources
                    ? ["Crisis resources"]
                    : [],
                  coping_strategies: [],
                  memory_stored: true, // Assume memory will be stored in background
                  timestamp: response.timestamp,
                  configuration_warning: false,
                  isUserMessage: false,
                }
              : msg
          )
        );
      } else {
        // Development mode: add complete message at once
        const newMessage: ChatMessage = {
          id: messageId,
          message: messageText,
          response: response.response,
          crisis_level: response.crisis_level || "SUPPORT",
          crisis_explanation: response.crisis_explanation || "",
          resources_provided: response.resources_provided || [],
          coping_strategies: response.coping_strategies || [],
          memory_stored: response.memory_stored || false,
          timestamp: response.timestamp,
          configuration_warning: response.configuration_warning,
        };
        setMessages((prev) => [...prev, newMessage]);

        // Handle legacy response format
        if (response.crisis_level === "CRISIS") {
          setCurrentCrisisData(response);
          setShowCrisisModal(true);
        }

        if (response.schedule_analysis?.should_suggest_scheduling) {
          setCurrentScheduleSuggestion(response.schedule_analysis);
          setShowScheduleModal(true);
        }

        if (response.action_plan_analysis?.should_suggest_action_plan) {
          setCurrentActionPlan(response.action_plan_analysis);
          setShowActionPlanModal(true);
        }
      }

      // Refresh memories
      if (response.memory_stored || response.background_task_id) {
        if (mode === "production") {
          // Invalidate queries for production mode
          queryClient.invalidateQueries({ queryKey: ["memories"] });
        } else if (
          loadMemories &&
          (activeTab === "memories" || activeTab === "anchors")
        ) {
          // Call loadMemories for development mode
          loadMemories();
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        message: messageText,
        response: "Sorry, I encountered an error. Please try again.",
        crisis_level: "SUPPORT",
        crisis_explanation: "Error occurred",
        resources_provided: [],
        coping_strategies: [],
        memory_stored: false,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : "Unknown error",
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleCreateActionPlan = async () => {
    if (!currentActionPlan?.background_task_id) {
      antMessage.error("No action plan data available");
      return;
    }

    setIsCreatingActionPlan(true);

    try {
      // Check if this is from multi-modal chat (has background_task_id)
      if (currentActionPlan.background_task_id) {
        // Use the new multi-modal API endpoint
        const response = await axiosInstance.post(
          `/chat-v2/action-plans/create-from-background?task_id=${currentActionPlan.background_task_id}`
        );

        if (response.data.action_plan_id) {
          antMessage.success("Action plan created successfully!");
          setShowActionPlanModal(false);

          // Navigate to the action plan page
          router.push(`/action-plans/${response.data.action_plan_id}`);
        }
      } else {
        // Fallback: create using the direct action plan API
        const actionPlanData = {
          title: currentActionPlan.action_plan?.name || "AI Generated Plan",
          description: currentActionPlan.action_plan?.description || "",
          plan_type: currentActionPlan.action_plan_type || "hybrid",
          priority: "medium",
          tags: [],
        };

        const response = await axiosInstance.post(
          "/action-plans/",
          actionPlanData
        );

        if (response.data.id) {
          antMessage.success("Action plan created successfully!");
          setShowActionPlanModal(false);

          // Navigate to the action plan page
          router.push(`/action-plans/${response.data.id}`);
        }
      }
    } catch (error) {
      console.error("Error creating action plan:", error);
      antMessage.error("Failed to create action plan. Please try again.");
    } finally {
      setIsCreatingActionPlan(false);
    }
  };

  // Switch to voice chat if voice mode is selected
  if (showVoiceToggle && communicationMode === "voice") {
    return (
      <VoiceChat
        onEndCall={() => setCommunicationMode("chat")}
        onSwitchToChat={() => setCommunicationMode("chat")}
      />
    );
  }

  return (
    <div className="h-full flex flex-col gap-4 overflow-hidden">
      {/* Communication Mode Selector - only show if enabled */}
      {showVoiceToggle && (
        <div className="w-full">
          <CommunicationModeSelector
            currentMode={communicationMode}
            onModeChange={setCommunicationMode}
            onStartConversation={() => {
              // Mode change is handled by onModeChange
            }}
            isConnected={true}
            isActive={false}
          />
        </div>
      )}

      {/* Test Scenarios - only show if enabled */}
      {showTestScenarios && (
        <div className="w-full">
          <div className="flex flex-col gap-4">
            <Card title="Test Scenarios">
              <Paragraph strong>Try these messages:</Paragraph>
              <Typography.Link
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setInputValue("I'm feeling anxious today");
                }}
              >
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  • "I'm feeling anxious today" (short-term)
                </Text>
              </Typography.Link>
              <br />
              <Typography.Link
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setInputValue("I got into Harvard today");
                }}
              >
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  • "I got into Harvard today" (long-term)
                </Text>
              </Typography.Link>
              <br />
              <Typography.Link
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setInputValue(
                    "My grandmother's garden represents peace to me"
                  );
                }}
              >
                <Text type="secondary" style={{ fontSize: "12px" }}>
                  • "My grandmother's garden represents peace to me" (anchor)
                </Text>
              </Typography.Link>
            </Card>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      <div className="flex-1 h-full">
        <Card
          className="h-full flex flex-col"
          classNames={{
            body: "h-full flex-1 !p-0 flex flex-col",
          }}
        >
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-auto p-4">
            {messages.length === 0 && (
              <Empty
                image={<Bot style={{ fontSize: "48px", color: "#bfbfbf" }} />}
                description={
                  <div className="flex flex-col gap-2">
                    <Text>Start your conversation with Nura</Text>
                    <Text type="secondary" style={{ fontSize: "12px" }}>
                      Your mental health companion is here to listen and support
                      you
                    </Text>
                  </div>
                }
              />
            )}

            {messages.map((msg) => (
              <div key={msg.id} style={{ marginBottom: "16px" }}>
                {/* User Message */}
                <div className="ml-auto w-fit flex flex-row-reverse items-start gap-2 mb-2">
                  <User className="h-6 w-6 mt-1 text-purple-500" />
                  <Card
                    size="small"
                    className="!bg-purple-50 !border-purple-300 !rounded-xl max-w-md"
                    classNames={{
                      body: "!p-3",
                    }}
                  >
                    <Paragraph className="!m-0">{msg.message}</Paragraph>
                  </Card>
                </div>

                {/* Assistant Response */}
                {msg.isUserMessage ? (
                  // Show loading state for messages waiting for response (production mode)
                  <div className="flex items-start gap-2 w-fit">
                    <Bot className="h-6 w-6 mt-1 text-blue-500" />
                    <Card
                      size="small"
                      className="!bg-blue-50 !border-blue-300 !rounded-xl"
                      classNames={{
                        body: "!p-3",
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <Spin
                          indicator={
                            <Loader2 className="h-4 w-4 animate-spin" />
                          }
                        />
                        <Text type="secondary">Nura is thinking...</Text>
                      </div>
                    </Card>
                  </div>
                ) : (
                  // Show complete response
                  <div className="flex items-start gap-2 w-fit">
                    <Bot className="h-6 w-6 mt-1 text-blue-500" />
                    <Card
                      size="small"
                      className="!bg-blue-50 !border-blue-300 !rounded-xl max-w-2xl"
                      classNames={{
                        body: "!p-3",
                      }}
                    >
                      <Paragraph className="!mb-2">{msg.response}</Paragraph>

                      {(msg.memory_stored || msg.configuration_warning) && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {msg.memory_stored && (
                            <Badge
                              style={{
                                backgroundColor: "#f6ffed",
                                color: "#52c41a",
                                borderColor: "#b7eb8f",
                              }}
                              count="Memory Stored ✓"
                            />
                          )}
                          {msg.configuration_warning && (
                            <Badge status="warning" text="Config Warning" />
                          )}
                        </div>
                      )}

                      {(msg.resources_provided.length > 0 ||
                        msg.coping_strategies.length > 0) && (
                        <div className="mt-3 text-xs text-gray-600">
                          {msg.resources_provided.length > 0 && (
                            <div className="mb-1">
                              <Text strong>Resources:</Text>{" "}
                              {msg.resources_provided.join(", ")}
                            </div>
                          )}
                          {msg.coping_strategies.length > 0 && (
                            <div>
                              <Text strong>Strategies:</Text>{" "}
                              {msg.coping_strategies.join(", ")}
                            </div>
                          )}
                        </div>
                      )}

                      {msg.error && (
                        <AntdAlert
                          message={`Error: ${msg.error}`}
                          type="error"
                          className="mt-2"
                        />
                      )}
                    </Card>
                  </div>
                )}
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSendMessage} className="flex gap-3">
              <Input
                value={inputValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setInputValue(e.target.value)
                }
                placeholder="Type your message to Nura..."
                disabled={isSending}
                onPressEnter={!isSending ? handleSendMessage : undefined}
                className="flex-1"
                size="large"
              />
              <Button
                htmlType="submit"
                type="primary"
                loading={isSending}
                disabled={!inputValue.trim()}
                icon={<Send className="h-4 w-4" />}
                size="large"
              />
            </form>
          </div>
        </Card>
      </div>

      {/* Crisis Intervention Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="text-red-600">Crisis Support Available</span>
          </div>
        }
        open={showCrisisModal}
        onCancel={() => setShowCrisisModal(false)}
        footer={[
          <Button key="continue" onClick={() => setShowCrisisModal(false)}>
            Continue Chatting
          </Button>,
          <Button
            key="hotline"
            type="primary"
            danger
            icon={<Phone className="h-4 w-4" />}
            onClick={() => window.open("tel:988")}
          >
            Call Crisis Hotline (988)
          </Button>,
        ]}
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            {currentCrisisData?.crisis_explanation}
          </p>

          <Divider />

          <div>
            <h4 className="font-semibold mb-2">Immediate Resources:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>National Suicide Prevention Lifeline: 988</li>
              <li>Crisis Text Line: Text HOME to 741741</li>
              <li>International Association for Suicide Prevention</li>
            </ul>
          </div>

          {currentCrisisData?.coping_strategies?.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">
                Immediate Coping Strategies:
              </h4>
              <div className="flex flex-wrap gap-1">
                {currentCrisisData.coping_strategies.map(
                  (strategy: string, index: number) => (
                    <Tag key={index} color="blue">
                      {strategy}
                    </Tag>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Action Plan Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-500" />
            <span className="text-blue-600">
              {currentActionPlan?.action_plan_type === "therapeutic_emotional"
                ? "Emotional Wellness Plan"
                : "Goal Achievement Plan"}
            </span>
          </div>
        }
        open={showActionPlanModal}
        onCancel={() => setShowActionPlanModal(false)}
        footer={[
          <Button key="dismiss" onClick={() => setShowActionPlanModal(false)}>
            Not Now
          </Button>,
          <Button
            key="create"
            type="primary"
            icon={<CheckCircle className="h-4 w-4" />}
            onClick={handleCreateActionPlan}
            loading={isCreatingActionPlan}
          >
            Create Action Plan
          </Button>,
        ]}
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            I noticed you might benefit from a structured action plan. Would you
            like me to help you create one?
          </p>

          {currentActionPlan?.extracted_action_plan && (
            <div className="bg-blue-50 p-3 rounded">
              <h4 className="font-semibold mb-2">Suggested Steps:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {/* Handle immediate actions from action plan object */}
                {currentActionPlan.extracted_action_plan.action_plan?.immediate_actions?.map(
                  (action: any, index: number) => (
                    <li key={index}>
                      <strong>{action.action}</strong>
                      {action.purpose && (
                        <span className="text-gray-600">
                          {" "}
                          - {action.purpose}
                        </span>
                      )}
                    </li>
                  )
                )}

                {/* Fallback for milestone goals if no immediate actions */}
                {(!currentActionPlan.extracted_action_plan.action_plan
                  ?.immediate_actions ||
                  currentActionPlan.extracted_action_plan.action_plan
                    .immediate_actions.length === 0) &&
                  currentActionPlan.extracted_action_plan.action_plan?.milestone_goals?.map(
                    (milestone: any, index: number) => (
                      <li key={`milestone-${index}`}>
                        <strong>{milestone.goal}</strong>
                        {milestone.timeframe && (
                          <span className="text-gray-600">
                            {" "}
                            ({milestone.timeframe})
                          </span>
                        )}
                      </li>
                    )
                  )}

                {/* Legacy fallback for steps array */}
                {currentActionPlan.extracted_action_plan.steps?.map(
                  (step: string, index: number) => (
                    <li key={`legacy-${index}`}>{step}</li>
                  )
                )}

                {/* Fallback for simple text format */}
                {typeof currentActionPlan.extracted_action_plan === "string" &&
                  currentActionPlan.extracted_action_plan
                    .split("\n")
                    .filter((step: string) => step.trim())
                    .map((step: string, index: number) => (
                      <li key={`text-${index}`}>{step.trim()}</li>
                    ))}
              </ul>
            </div>
          )}
        </div>
      </Modal>

      {/* Schedule Suggestion Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-green-500" />
            <span className="text-green-600">Wellness Check-in Suggestion</span>
          </div>
        }
        open={showScheduleModal}
        onCancel={() => setShowScheduleModal(false)}
        footer={[
          <Button key="dismiss" onClick={() => setShowScheduleModal(false)}>
            Maybe Later
          </Button>,
          <Button
            key="schedule"
            type="primary"
            icon={<Clock className="h-4 w-4" />}
            onClick={() => {
              // TODO: Integrate with scheduling system
              setShowScheduleModal(false);
            }}
          >
            Schedule Check-in
          </Button>,
        ]}
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Based on our conversation, I think it would be helpful to schedule a
            follow-up wellness check-in.
          </p>

          {currentScheduleSuggestion?.schedule_opportunity_type && (
            <div className="bg-green-50 p-3 rounded">
              <h4 className="font-semibold mb-2">Suggested Check-in Type:</h4>
              <Tag color="green">
                {currentScheduleSuggestion.schedule_opportunity_type}
              </Tag>
            </div>
          )}

          {currentScheduleSuggestion?.extracted_schedule && (
            <div className="bg-gray-50 p-3 rounded">
              <h4 className="font-semibold mb-2">Suggested Time:</h4>
              <p className="text-sm">
                {JSON.stringify(
                  currentScheduleSuggestion.extracted_schedule,
                  null,
                  2
                )}
              </p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Chat;
