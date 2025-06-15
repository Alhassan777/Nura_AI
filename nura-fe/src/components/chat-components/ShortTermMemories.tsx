"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty, Spin, Tag, Space } from "antd";
import { Clock, MessageCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { MemoryContext } from "./types";

interface ShortTermMemoriesProps {
  userId: string;
  conversationId: string;
  isLoadingMemories: boolean;
  memoryContext: MemoryContext | null;
  loadMemories?: () => void;
}

export const ShortTermMemories: React.FC<ShortTermMemoriesProps> = ({
  userId,
  conversationId,
  isLoadingMemories,
  memoryContext,
  loadMemories,
}) => {
  const shortTermMemories = memoryContext?.short_term || [];

  if (isLoadingMemories) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-blue-500" />
            <span>Short-term Memories (This Session)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <Spin size="large" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (shortTermMemories.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-blue-500" />
            <span>Short-term Memories (This Session)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            image={<Clock className="mx-auto h-12 w-12 text-blue-500" />}
            description={
              <div className="text-center">
                <p className="text-gray-600">No short-term memories yet</p>
                <p className="text-sm text-gray-400">
                  Recent conversation context will appear here
                </p>
              </div>
            }
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Clock className="h-5 w-5 text-blue-500" />
          <span>Short-term Memories (This Session)</span>
          <Tag color="blue">{shortTermMemories.length}</Tag>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {shortTermMemories.map((memory, index) => {
            // Ensure unique keys by combining ID with index and memory type
            const uniqueKey = memory.id
              ? `short-term-${memory.id}-${index}`
              : `short-term-memory-${index}`;

            return (
              <Card key={uniqueKey} className="bg-blue-50 border-blue-200">
                <CardContent className="p-4">
                  <div className="flex items-start space-x-3">
                    <MessageCircle className="h-4 w-4 text-blue-500 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-gray-800 mb-2">{memory.content}</p>
                      <div className="flex items-center justify-between">
                        <Space size="small">
                          <Tag color="blue">Short-term</Tag>
                          {memory.metadata?.memory_category && (
                            <Tag color="default">
                              {memory.metadata.memory_category}
                            </Tag>
                          )}
                        </Space>
                        <span className="text-xs text-gray-500">
                          {memory.timestamp
                            ? formatDistanceToNow(new Date(memory.timestamp), {
                                addSuffix: true,
                              })
                            : "Recently"}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
