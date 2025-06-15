"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Database, Brain, Heart, TrendingUp } from "lucide-react";
import { useMemoryStats } from "../../services/hooks/use-memory";

interface MemoryStatsProps {
  userId: string;
}

export const MemoryStats: React.FC<MemoryStatsProps> = ({ userId }) => {
  const { data: stats, isLoading } = useMemoryStats(userId);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading statistics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-600">
            No memory statistics available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Remove percentage calculations - we want to show numbers only

  // Safe access to recent_activity with defaults
  const recentActivity = stats.recent_activity || {
    memories_added_this_week: 0,
    memories_added_today: 0,
    last_memory_timestamp: null,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Memories */}
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Total Memories
              </p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Database className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Long-term Memories */}
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Long-term</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats.long_term}
              </p>
              <p className="text-xs text-gray-500 mt-1">Persistent memories</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emotional Anchors */}
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Emotional Anchors
              </p>
              <p className="text-2xl font-bold text-pink-600">
                {stats.emotional_anchors || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">Symbolic memories</p>
            </div>
            <div className="p-3 bg-pink-100 rounded-full">
              <Heart className="h-6 w-6 text-pink-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">This Week</p>
              <p className="text-2xl font-bold text-green-600">
                {recentActivity.memories_added_this_week}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {recentActivity.memories_added_today} today
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
