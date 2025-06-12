"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Input, Select, List, Tag, Empty, Modal, Drawer } from "antd";
import {
  Search,
  Filter,
  Download,
  Trash2,
  Calendar,
  Bot,
  MessageSquare,
  AlertTriangle,
  Phone,
  MessageCircle,
  FileText,
  Clock,
  Target,
  Eye,
} from "lucide-react";
import {
  useChatHistory,
  useClearChatHistory,
  useExportChatHistory,
} from "@/services/hooks/use-chat-history";

const { Option } = Select;

interface ChatSession {
  id: string;
  title: string;
  type: "text" | "voice";
  created_at: string;
  message_count?: number;
  call_duration?: number;
  last_message: string;
  crisis_detected: boolean;
  action_plans_created: number;
  wellness_checks_scheduled: number;
  summary: string;
  transcript?: {
    available: boolean;
    preview: string;
    word_count: number;
    confidence_score: number;
  };
  mood_analysis: {
    dominant_emotion: string;
    emotional_intensity: number;
    improvement_noted: boolean;
  };
}

export default function ChatHistoryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(
    null
  );
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);

  const { data: sessions, isLoading } = useChatHistory();
  const clearHistoryMutation = useClearChatHistory();
  const exportHistoryMutation = useExportChatHistory();

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const getFilteredSessions = () => {
    if (!sessions) return [];

    let filtered = sessions.filter((session: any) => {
      const matchesSearch =
        session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.summary.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesSearch;
    });

    switch (activeFilter) {
      case "crisis":
        return filtered.filter((s: any) => s.crisis_detected);
      case "voice":
        return filtered.filter((s: any) => s.type === "voice");
      case "text":
        return filtered.filter((s: any) => s.type === "text");
      case "action_plans":
        return filtered.filter((s: any) => s.action_plans_created > 0);
      default:
        return filtered;
    }
  };

  const filteredSessions = getFilteredSessions();

  const handleClearHistory = () => {
    clearHistoryMutation.mutate();
    setShowClearModal(false);
  };

  const handleExportHistory = () => {
    exportHistoryMutation.mutate();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <MessageSquare className="h-8 w-8 text-blue-600" />
        <h1 className="text-3xl font-bold text-gray-900">Chat History</h1>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Sessions</p>
                <p className="text-2xl font-bold">{sessions?.length || 0}</p>
              </div>
              <MessageCircle className="h-8 w-8 text-blue-500" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Voice Calls</p>
                <p className="text-2xl font-bold">
                  {sessions?.filter((s: any) => s.type === "voice").length || 0}
                </p>
              </div>
              <Phone className="h-8 w-8 text-green-500" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Crisis Interventions</p>
                <p className="text-2xl font-bold">
                  {sessions?.filter((s: any) => s.crisis_detected).length || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Action Plans</p>
                <p className="text-2xl font-bold">
                  {sessions?.reduce(
                    (sum: number, s: any) =>
                      sum + (s.action_plans_created || 0),
                    0
                  ) || 0}
                </p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <div className="p-4">
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1">
              <Input
                placeholder="Search conversations..."
                prefix={<Search className="h-4 w-4 text-gray-400" />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <Select
                value={activeFilter}
                onChange={setActiveFilter}
                style={{ width: 200 }}
                prefix={<Filter className="h-4 w-4" />}
              >
                <Option value="all">All Sessions</Option>
                <Option value="voice">Voice Calls</Option>
                <Option value="text">Text Chats</Option>
                <Option value="crisis">Crisis Interventions</Option>
                <Option value="action_plans">With Action Plans</Option>
              </Select>
              <Button
                icon={<Download className="h-4 w-4" />}
                onClick={handleExportHistory}
                loading={exportHistoryMutation.isPending}
              >
                Export
              </Button>
              <Button
                danger
                icon={<Trash2 className="h-4 w-4" />}
                onClick={() => setShowClearModal(true)}
              >
                Clear All
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Session List */}
      <Card>
        <div className="p-4">
          {isLoading ? (
            <div className="text-center py-8">Loading chat history...</div>
          ) : filteredSessions.length > 0 ? (
            <List
              dataSource={filteredSessions}
              renderItem={(session: any) => (
                <List.Item
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => {
                    setSelectedSession(session);
                    setShowSessionModal(true);
                  }}
                  actions={[
                    <Button
                      key="view"
                      type="text"
                      icon={<Eye className="h-4 w-4" />}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSession(session);
                        setShowSessionModal(true);
                      }}
                    >
                      View
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <div
                        className={`p-2 rounded-full ${
                          session.type === "voice"
                            ? "bg-green-100"
                            : "bg-blue-100"
                        }`}
                      >
                        {session.type === "voice" ? (
                          <Phone className="h-5 w-5 text-green-600" />
                        ) : (
                          <MessageCircle className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                    }
                    title={
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{session.title}</span>
                        <div className="flex items-center space-x-2">
                          {session.crisis_detected && (
                            <Tag
                              color="red"
                              icon={<AlertTriangle className="h-3 w-3" />}
                            >
                              Crisis
                            </Tag>
                          )}
                          {session.action_plans_created > 0 && (
                            <Tag color="purple">
                              {session.action_plans_created} Action Plans
                            </Tag>
                          )}
                          {session.type === "voice" && session.transcript && (
                            <Tag
                              color="green"
                              icon={<FileText className="h-3 w-3" />}
                            >
                              Transcript
                            </Tag>
                          )}
                        </div>
                      </div>
                    }
                    description={
                      <div className="space-y-1">
                        <p className="text-gray-600 text-sm line-clamp-2">
                          {session.summary}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            {formatDate(session.created_at)}
                          </span>
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {session.type === "voice"
                              ? formatDuration(session.call_duration || 0)
                              : `${session.message_count || 0} messages`}
                          </span>
                          <span>
                            Mood: {session.mood_analysis?.dominant_emotion}
                          </span>
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium mb-2">
                No conversations found
              </h3>
              <p>
                {searchTerm || activeFilter !== "all"
                  ? "Try adjusting your search or filters"
                  : "Start chatting with Nura to see your conversation history here"}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Session Detail Modal */}
      <Modal
        title={
          selectedSession
            ? `${selectedSession.title} Details`
            : "Session Details"
        }
        open={showSessionModal}
        onCancel={() => setShowSessionModal(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setShowSessionModal(false)}>
            Close
          </Button>,
          selectedSession?.type === "voice" && selectedSession?.transcript && (
            <Button
              key="download"
              type="primary"
              icon={<Download className="h-4 w-4" />}
            >
              Download Transcript
            </Button>
          ),
        ]}
      >
        {selectedSession && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700">Session Type</h4>
                <div className="flex items-center gap-2">
                  {selectedSession.type === "voice" ? (
                    <Phone className="h-4 w-4 text-green-600" />
                  ) : (
                    <MessageCircle className="h-4 w-4 text-blue-600" />
                  )}
                  <span className="capitalize">
                    {selectedSession.type}{" "}
                    {selectedSession.type === "voice" ? "Call" : "Chat"}
                  </span>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">Duration/Length</h4>
                <p className="text-gray-600">
                  {selectedSession.type === "voice"
                    ? formatDuration(selectedSession.call_duration || 0)
                    : `${selectedSession.message_count || 0} messages`}
                </p>
              </div>
            </div>

            {/* Voice Call Transcript */}
            {selectedSession.type === "voice" && selectedSession.transcript && (
              <div>
                <h4 className="font-medium text-gray-700 mb-2">
                  Conversation Transcript
                </h4>
                <div className="bg-gray-50 p-4 rounded border max-h-96 overflow-y-auto">
                  <div className="mb-2 text-sm text-gray-600">
                    Accuracy:{" "}
                    {Math.round(
                      selectedSession.transcript.confidence_score * 100
                    )}
                    % | Words: {selectedSession.transcript.word_count}
                  </div>
                  <div className="whitespace-pre-wrap text-sm">
                    {selectedSession.transcript.preview}
                  </div>
                </div>
              </div>
            )}

            {/* Mood Analysis */}
            <div>
              <h4 className="font-medium text-gray-700 mb-2">
                Emotional Analysis
              </h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-sm text-gray-600">
                    Dominant Emotion
                  </span>
                  <p className="font-medium capitalize">
                    {selectedSession.mood_analysis?.dominant_emotion}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Intensity</span>
                  <p className="font-medium">
                    {selectedSession.mood_analysis?.emotional_intensity}/10
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Improvement</span>
                  <Tag
                    color={
                      selectedSession.mood_analysis?.improvement_noted
                        ? "green"
                        : "orange"
                    }
                  >
                    {selectedSession.mood_analysis?.improvement_noted
                      ? "Noted"
                      : "None"}
                  </Tag>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-700 mb-2">Summary</h4>
              <p className="text-gray-600">{selectedSession.summary}</p>
            </div>
          </div>
        )}
      </Modal>

      {/* Clear History Confirmation Modal */}
      <Modal
        title="Clear Chat History"
        open={showClearModal}
        onCancel={() => setShowClearModal(false)}
        onOk={handleClearHistory}
        okText="Clear All"
        okButtonProps={{ danger: true }}
        confirmLoading={clearHistoryMutation.isPending}
      >
        <p>
          Are you sure you want to clear all chat history? This action cannot be
          undone.
        </p>
      </Modal>
    </div>
  );
}
