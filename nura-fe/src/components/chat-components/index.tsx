"use client";

import { useState, useEffect, useCallback } from "react";
import { Tabs as AntdTabs, Segmented, Space, Button } from "antd";
import {
  Bot,
  Brain,
  Database,
  Shield,
  Clock,
  Heart,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import MemoryPrivacyManager from "@/components/chat-components/MemoryPrivacyManager";
import { MemoryContext, MemoryStats } from "./types";
import ServerHealthStatus from "./server-health-status";
import Chat from "./chat";
import { MemoryStatistics } from "./memory-statistics";
import EmotionalAnchors from "./emotional-anchors";
import { useSendMessage } from "@/services/hooks";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import axiosInstance from "@/services/apis";
import { ShortTermMemories } from "./ShortTermMemories";
import { LongTermMemories } from "./LongTermMemories";
import { EmotionalAnchorMemories } from "./EmotionalAnchorMemories";

export const ChatComponent = () => {
  const [userId] = useState(() => `test-user-${Date.now()}`);

  // Use a persistent conversation ID that survives page reloads for the same session
  const [conversationId] = useState(() => {
    // Try to get existing conversation ID from sessionStorage
    if (typeof window !== "undefined") {
      const existingId = sessionStorage.getItem("currentConversationId");
      if (existingId) {
        return existingId;
      }
    }

    // Create new conversation ID for this session
    const newConversationId = `conversation-${Date.now()}-${Math.random()
      .toString(36)
      .substring(2)}`;

    // Store it for this session
    if (typeof window !== "undefined") {
      sessionStorage.setItem("currentConversationId", newConversationId);
    }

    return newConversationId;
  });

  const [activeTab, setActiveTab] = useState("chat");

  const [memoryContext, setMemoryContext] = useState<MemoryContext | null>(
    null
  );
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);

  const startNewConversation = () => {
    const newConversationId = `conversation-${Date.now()}-${Math.random()
      .toString(36)
      .substring(2)}`;

    // Update sessionStorage with new conversation ID
    if (typeof window !== "undefined") {
      sessionStorage.setItem("currentConversationId", newConversationId);
    }

    // Force page reload to use new conversation ID
    window.location.reload();
  };

  const { mutateAsync: sendMessage } = useSendMessage();

  const loadMemories = useCallback(async () => {
    setIsLoadingMemories(true);
    try {
      // Load memories ONLY for this specific conversation
      const [allMemoriesResponse, contextResponse, statsResponse] =
        await Promise.all([
          axiosInstance.get(
            `/memory/all-long-term?conversation_id=${conversationId}`
          ),
          axiosInstance.post("/memory/context", {
            query: "",
            conversation_id: conversationId,
          }),
          axiosInstance.get("/memory/stats"),
        ]);

      if (
        allMemoriesResponse.status === 200 &&
        contextResponse.status === 200
      ) {
        const allMemoriesData = allMemoriesResponse.data;
        const contextData = contextResponse.data;
        const memoriesCount =
          (allMemoriesData.regular_memories?.length || 0) +
          (allMemoriesData.emotional_anchors?.length || 0);

        setMemoryContext({
          short_term: contextData.context?.short_term || [],
          long_term: allMemoriesData.regular_memories || [],
          emotional_anchors: allMemoriesData.emotional_anchors || [],
          digest: `${memoriesCount} memories found in this conversation only`,
        });

        console.log(
          `Loaded ${memoriesCount} memories for conversation: ${conversationId}`
        );
      }

      if (statsResponse.status === 200) {
        const statsData = statsResponse.data;
        setMemoryStats(statsData.stats);
      }
    } catch (error) {
      console.error("Error loading conversation memories:", error);
    } finally {
      setIsLoadingMemories(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (activeTab !== "chat") {
      loadMemories();
    }
  }, [activeTab, loadMemories]);

  const tabItems = [
    {
      key: "chat",
      label: (
        <Space>
          <Bot />
          Chat
        </Space>
      ),
      children: (
        <Chat
          mode="development"
          showTestScenarios={true}
          showVoiceToggle={true}
          activeTab="chat"
          loadMemories={loadMemories}
          conversationId={conversationId}
        />
      ),
    },
    {
      key: "short-term",
      label: (
        <Space>
          <Clock />
          Short-term
        </Space>
      ),
      children: (
        <ShortTermMemories
          userId={userId}
          conversationId={conversationId}
          isLoadingMemories={isLoadingMemories}
          memoryContext={memoryContext}
          loadMemories={loadMemories}
        />
      ),
    },
    {
      key: "long-term",
      label: (
        <Space>
          <Brain />
          Long-term
        </Space>
      ),
      children: (
        <LongTermMemories
          userId={userId}
          conversationId={conversationId}
          isLoadingMemories={isLoadingMemories}
          memoryContext={memoryContext}
          loadMemories={loadMemories}
        />
      ),
    },
    {
      key: "emotional-anchors",
      label: (
        <Space>
          <Heart />
          Emotional Anchors
        </Space>
      ),
      children: (
        <EmotionalAnchorMemories
          userId={userId}
          conversationId={conversationId}
          isLoadingMemories={isLoadingMemories}
          memoryContext={memoryContext}
          loadMemories={loadMemories}
        />
      ),
    },
  ];

  return (
    <div className="w-full min-h-screen h-fit flex flex-col py-4">
      <ServerHealthStatus userId={userId} />

      {/* Conversation Info */}
      <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="text-sm text-gray-700">
          <span className="font-medium">Current Session:</span>{" "}
          {conversationId.slice(-8)}...
          <span className="text-xs text-gray-500 ml-2">
            (persists until "New Chat")
          </span>
        </div>
        <div className="text-xs text-blue-600 mt-1 font-medium flex items-center justify-between">
          <span>💡 Memory tabs show only memories from THIS conversation.</span>
          <div className="flex gap-2">
            <Button
              onClick={startNewConversation}
              size="small"
              type="default"
              className="text-xs h-6"
            >
              New Chat
            </Button>
            <Link href="/memories">
              <Button
                type="link"
                size="small"
                icon={<ExternalLink className="h-3 w-3" />}
                className="text-blue-600 hover:text-blue-800 p-0 h-auto"
              >
                View All Memories
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex flex-col flex-1 w-full mt-4"
      >
        <TabsList className="w-full justify-start rounded-xl border border-gray-100 bg-gray-50 gap-4 overflow-x-auto h-fit">
          {tabItems.map((item) => (
            <TabsTrigger
              key={item.key}
              value={item.key}
              className={cn(
                "rounded-lg p-2 bg-transparent cursor-pointer hover:bg-white border border-transparent hover:border-gray-200 hover:shadow-sm duration-300 transition-all",
                activeTab === item.key &&
                  "border border-gray-200 shadow-sm bg-white"
              )}
            >
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabItems.map((item) => (
          <TabsContent
            key={item.key}
            value={item.key}
            className="flex flex-col flex-1 overflow-y-auto ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {item.children}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};
