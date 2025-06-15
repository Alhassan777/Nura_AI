"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Button,
  Input,
  Select,
  Checkbox,
  Modal,
  message,
  Tag,
  Avatar,
  Empty,
  Space,
  Pagination,
} from "antd";
import {
  SearchOutlined,
  DeleteOutlined,
  HeartOutlined,
  DatabaseOutlined,
  ExportOutlined,
  FilterOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import {
  Search,
  Calendar,
  Clock,
  Database,
  Heart,
  Filter,
  Download,
  Trash2,
  Archive,
  Star,
} from "lucide-react";
import { MemorySearchFilter } from "@/components/memory/MemorySearchFilter";
import { MemoryCard } from "@/components/memory/MemoryCard";
import { MemoryStats } from "@/components/memory/MemoryStats";
import { BulkOperations } from "@/components/memory/BulkOperations";
import { PendingConsentMemories } from "@/components/memory/PendingConsentMemories";
import { memoryApi } from "@/services/apis/memory";
import {
  useDeleteMemory,
  useDeleteMultipleMemories,
  useExportMemories,
  useUpdateMemoryMetadata,
  useConvertToAnchor,
} from "@/services/hooks/use-memory";

export default function MemoriesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedMemories, setSelectedMemories] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [memories, setMemories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalMemories, setTotalMemories] = useState(0);

  // TODO: Replace with actual user ID from auth context
  const userId = "test-user";

  // React Query hooks for memory operations
  const deleteMemoryMutation = useDeleteMemory();
  const deleteMultipleMemoriesMutation = useDeleteMultipleMemories();
  const exportMemoriesMutation = useExportMemories();
  const updateMemoryMutation = useUpdateMemoryMetadata();
  const convertToAnchorMutation = useConvertToAnchor();

  // Load all memories from all conversations
  useEffect(() => {
    const loadAllMemories = async () => {
      setIsLoading(true);
      try {
        // Load ALL memories from ALL conversations (no conversation_id filter)
        const allMemoriesResponse =
          await memoryApi.getAllMemoriesFromAllChats();

        // Combine regular memories and emotional anchors
        const allMemories = [
          ...(allMemoriesResponse.regular_memories || []),
          ...(allMemoriesResponse.emotional_anchors || []),
        ];

        // Deduplicate memories by content to handle component-based duplicates
        const deduplicatedMemories = allMemories.reduce((acc, memory) => {
          // Use content as deduplication key, with a fallback to ID
          const dedupKey = memory.content || memory.id;
          if (
            !acc.find(
              (existing) =>
                existing.content === dedupKey || existing.id === memory.id
            )
          ) {
            acc.push(memory);
          }
          return acc;
        }, []);

        setMemories(deduplicatedMemories);
        setTotalMemories(deduplicatedMemories.length);

        console.log(
          `Loaded ${
            deduplicatedMemories.length
          } memories from all conversations for Memory Vault (${
            allMemories.length - deduplicatedMemories.length
          } duplicates removed)`
        );
      } catch (error) {
        console.error("Error loading memories for Memory Vault:", error);
        message.error("Failed to load memories");
      } finally {
        setIsLoading(false);
      }
    };

    loadAllMemories();
  }, []);

  const handleDeleteMemory = (memoryId: string) => {
    Modal.confirm({
      title: "Delete Memory",
      content:
        "Are you sure you want to delete this memory? This action cannot be undone.",
      okText: "Delete",
      okType: "danger",
      cancelText: "Cancel",
      onOk: async () => {
        try {
          await deleteMemoryMutation.mutateAsync(memoryId);
          // Remove from local state immediately for better UX
          setMemories((prev) => prev.filter((m) => m.id !== memoryId));
          setTotalMemories((prev) => prev - 1);
          message.success("Memory deleted successfully");
        } catch (error) {
          console.error("Error deleting memory:", error);
          message.error("Failed to delete memory");
        }
      },
    });
  };

  const handleBulkDelete = () => {
    if (selectedMemories.length === 0) {
      message.warning("Please select memories to delete");
      return;
    }

    Modal.confirm({
      title: "Delete Selected Memories",
      content: `Are you sure you want to delete ${selectedMemories.length} selected memories? This action cannot be undone.`,
      okText: "Delete All",
      okType: "danger",
      cancelText: "Cancel",
      onOk: async () => {
        try {
          await deleteMultipleMemoriesMutation.mutateAsync(selectedMemories);
          // Remove from local state immediately for better UX
          setMemories((prev) =>
            prev.filter((m) => !selectedMemories.includes(m.id))
          );
          setTotalMemories((prev) => prev - selectedMemories.length);
          const deletedCount = selectedMemories.length;
          setSelectedMemories([]);
          message.success(`${deletedCount} memories deleted successfully`);
        } catch (error) {
          console.error("Error deleting memories:", error);
          message.error("Failed to delete selected memories");
        }
      },
    });
  };

  const handleExportMemories = async () => {
    try {
      message.info("Exporting memories... Download will start shortly.");
      await exportMemoriesMutation.mutateAsync({ userId, format: "json" });
      message.success("Memories exported successfully!");
    } catch (error) {
      console.error("Error exporting memories:", error);
      message.error("Failed to export memories");
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedMemories(memories.map((m) => m.id));
    } else {
      setSelectedMemories([]);
    }
  };

  const handleEditMemory = async (memoryId: string, updates: any) => {
    try {
      await updateMemoryMutation.mutateAsync({ memoryId, metadata: updates });
      // Update local state
      setMemories((prev) =>
        prev.map((m) => (m.id === memoryId ? { ...m, ...updates } : m))
      );
      message.success("Memory updated successfully");
    } catch (error) {
      console.error("Error updating memory:", error);
      message.error("Failed to update memory");
    }
  };

  const handleConvertToAnchor = async (memoryId: string) => {
    try {
      await convertToAnchorMutation.mutateAsync({ memoryId });
      // Update local state to reflect the change
      setMemories((prev) =>
        prev.map((m) =>
          m.id === memoryId
            ? {
                ...m,
                memory_category: "emotional_anchor",
                is_emotional_anchor: true,
              }
            : m
        )
      );
      message.success("Memory converted to emotional anchor successfully");
    } catch (error) {
      console.error("Error converting memory to anchor:", error);
      message.error("Failed to convert memory to emotional anchor");
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Memory Vault
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            All your long-term memories and emotional anchors from every
            conversation
          </p>
        </div>

        <div className="flex space-x-2">
          <Button
            icon={<FilterOutlined />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExportMemories}>
            Export
          </Button>
        </div>
      </div>

      {/* Memory Statistics */}
      <MemoryStats userId={userId} />

      {/* Pending Consent Memories */}
      <PendingConsentMemories userId={userId} />

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col space-y-4">
            {/* Main Search */}
            <div className="flex space-x-4">
              <Input
                size="large"
                placeholder="Search memories..."
                prefix={<SearchOutlined />}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              <Select
                size="large"
                value={selectedCategory}
                onChange={setSelectedCategory}
                style={{ width: 200 }}
              >
                <Select.Option value="all">All Categories</Select.Option>
                <Select.Option value="long_term">
                  Long-term Memories
                </Select.Option>
                <Select.Option value="emotional_anchors">
                  Emotional Anchors
                </Select.Option>
                <Select.Option value="achievements">Achievements</Select.Option>
                <Select.Option value="relationships">
                  Relationships
                </Select.Option>
                <Select.Option value="personal_growth">
                  Personal Growth
                </Select.Option>
              </Select>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <MemorySearchFilter
                onFilterChange={(filters) => console.log("Filters:", filters)}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {/* Bulk Operations */}
      {selectedMemories.length > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <BulkOperations
              selectedCount={selectedMemories.length}
              onBulkDelete={handleBulkDelete}
              onBulkExport={() => console.log("Bulk export")}
              onBulkTag={() => console.log("Bulk tag")}
              onDeselectAll={() => setSelectedMemories([])}
            />
          </CardContent>
        </Card>
      )}

      {/* Memory List */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <span>Your Memories ({totalMemories})</span>
            </CardTitle>

            {memories.length > 0 && (
              <Checkbox
                checked={selectedMemories.length === memories.length}
                indeterminate={
                  selectedMemories.length > 0 &&
                  selectedMemories.length < memories.length
                }
                onChange={(e) => handleSelectAll(e.target.checked)}
              >
                Select All
              </Checkbox>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading memories...</p>
            </div>
          ) : memories.length === 0 ? (
            <Empty
              image={<Database className="mx-auto h-16 w-16 text-gray-400" />}
              description={
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No memories found
                  </h3>
                  <p className="text-gray-600">
                    {searchQuery
                      ? "Try adjusting your search or filters"
                      : "Start chatting with Nura to create meaningful memories"}
                  </p>
                </div>
              }
            />
          ) : (
            <div className="space-y-4">
              {memories.map((memory, index) => {
                // Ensure unique keys by combining ID with index and type
                const uniqueKey = memory.id
                  ? `${memory.id}-${index}`
                  : `memory-${index}`;
                return (
                  <MemoryCard
                    key={uniqueKey}
                    memory={memory}
                    isSelected={selectedMemories.includes(memory.id)}
                    onSelect={(selected) => {
                      if (selected) {
                        setSelectedMemories((prev) => [...prev, memory.id]);
                      } else {
                        setSelectedMemories((prev) =>
                          prev.filter((id) => id !== memory.id)
                        );
                      }
                    }}
                    onDelete={handleDeleteMemory}
                    onEdit={handleEditMemory}
                    onConvertToAnchor={handleConvertToAnchor}
                  />
                );
              })}
            </div>
          )}

          {/* Pagination */}
          {totalMemories > pageSize && (
            <div className="mt-6 flex justify-center">
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={totalMemories}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) =>
                  `${range[0]}-${range[1]} of ${total} memories`
                }
                onChange={(page, size) => {
                  setCurrentPage(page);
                  setPageSize(size || 20);
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
