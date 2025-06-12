"use client";

import { useState, useEffect, useCallback } from "react";
import { Tabs as AntdTabs, Segmented, Space } from "antd";
import { Bot, Brain, Database, Shield, Clock, Heart } from "lucide-react";
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
  const [conversationId] = useState(
    () =>
      `conversation-${Date.now()}-${Math.random().toString(36).substring(2)}`
  );
  const [activeTab, setActiveTab] = useState("chat");

  const [memoryContext, setMemoryContext] = useState<MemoryContext | null>(
    null
  );
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);

  const { mutateAsync: sendMessage } = useSendMessage();

  const loadMemories = useCallback(async () => {
    setIsLoadingMemories(true);
    try {
      // Load memories for this specific conversation
      const allMemoriesResponse = await axiosInstance.get(
        `/memory/all-long-term?conversation_id=${conversationId}`
      );
      const contextResponse = await axiosInstance.post("/memory/context", {
        query: "",
        conversation_id: conversationId,
      });

      if (
        allMemoriesResponse.status === 200 &&
        contextResponse.status === 200
      ) {
        const allMemoriesData = allMemoriesResponse.data;
        const contextData = contextResponse.data;

        setMemoryContext({
          short_term: contextData.context?.short_term || [],
          long_term: allMemoriesData.regular_memories || [],
          emotional_anchors: allMemoriesData.emotional_anchors || [],
          digest: `${
            allMemoriesData.counts?.total || 0
          } total memories found in this conversation`,
        });
      }

      const statsResponse = await axiosInstance.get("/memory/stats");

      if (statsResponse.status === 200) {
        const statsData = statsResponse.data;
        setMemoryStats(statsData.stats);
      }
    } catch (error) {
      console.error("Error loading memories:", error);
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
      <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
        <div className="text-sm text-gray-600">
          <span className="font-medium">Conversation:</span> {conversationId}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Memories in this conversation will be filtered to this chat session
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
