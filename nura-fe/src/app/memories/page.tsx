"use client";

import { useState } from "react";
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

export default function MemoriesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedMemories, setSelectedMemories] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // TODO: Replace with actual user ID from auth context
  const userId = "test-user";

  // Placeholder data - will be replaced with real hooks
  const memories: any[] = [];
  const isLoading = false;
  const totalMemories = 0;

  const handleDeleteMemory = (memoryId: string) => {
    Modal.confirm({
      title: "Delete Memory",
      content:
        "Are you sure you want to delete this memory? This action cannot be undone.",
      okText: "Delete",
      okType: "danger",
      cancelText: "Cancel",
      onOk: () => {
        // deleteMemoryMutation.mutate(memoryId);
        message.success("Memory deleted successfully");
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
      onOk: () => {
        // deleteMultipleMemoriesMutation.mutate(selectedMemories);
        setSelectedMemories([]);
        message.success(
          `${selectedMemories.length} memories deleted successfully`
        );
      },
    });
  };

  const handleExportMemories = () => {
    // exportMemoriesMutation.mutate({ userId, format: 'json' });
    message.info("Exporting memories... Download will start shortly.");
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedMemories(memories.map((m) => m.id));
    } else {
      setSelectedMemories([]);
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
            Manage your long-term memories and emotional anchors
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
              {memories.map((memory) => (
                <MemoryCard
                  key={memory.id}
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
                  onEdit={(id, updates) =>
                    console.log("Edit memory:", id, updates)
                  }
                  onConvertToAnchor={(id) =>
                    console.log("Convert to anchor:", id)
                  }
                />
              ))}
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
