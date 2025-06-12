"use client";

import { useState } from "react";
import { Card, Select, DatePicker, Switch, Button, Row, Col, Tag } from "antd";
import { FilterOutlined, ClearOutlined } from "@ant-design/icons";

const { RangePicker } = DatePicker;

interface FilterOptions {
  storageType: "all" | "long_term";
  includeAnchors: boolean;
  dateRange: [string, string] | null;
  hasTagged: boolean;
  hasPII: boolean;
  relevanceThreshold: number;
}

interface MemorySearchFilterProps {
  onFilterChange: (filters: FilterOptions) => void;
}

export const MemorySearchFilter: React.FC<MemorySearchFilterProps> = ({
  onFilterChange,
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    storageType: "all",
    includeAnchors: true,
    dateRange: null,
    hasTagged: false,
    hasPII: false,
    relevanceThreshold: 0,
  });

  const handleFilterChange = (key: keyof FilterOptions, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const defaultFilters: FilterOptions = {
      storageType: "all",
      includeAnchors: true,
      dateRange: null,
      hasTagged: false,
      hasPII: false,
      relevanceThreshold: 0,
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  return (
    <Card className="bg-gray-50 border-gray-200">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-700 flex items-center">
            <FilterOutlined className="mr-2" />
            Advanced Filters
          </h4>
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={clearFilters}
          >
            Clear All
          </Button>
        </div>

        <Row gutter={[16, 16]}>
          {/* Storage Type */}
          <Col xs={24} sm={12} md={6}>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Memory Type
              </label>
              <Select
                value={filters.storageType}
                onChange={(value) => handleFilterChange("storageType", value)}
                className="w-full"
              >
                <Select.Option value="all">All Types</Select.Option>
                <Select.Option value="long_term">Long-term</Select.Option>
              </Select>
            </div>
          </Col>

          {/* Date Range */}
          <Col xs={24} sm={12} md={8}>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Date Range
              </label>
              <RangePicker
                className="w-full"
                onChange={(dates) => {
                  if (dates && dates[0] && dates[1]) {
                    handleFilterChange("dateRange", [
                      dates[0].toISOString(),
                      dates[1].toISOString(),
                    ]);
                  } else {
                    handleFilterChange("dateRange", null);
                  }
                }}
              />
            </div>
          </Col>

          {/* Relevance Threshold */}
          <Col xs={24} sm={12} md={6}>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Min Relevance (%)
              </label>
              <Select
                value={filters.relevanceThreshold}
                onChange={(value) =>
                  handleFilterChange("relevanceThreshold", value)
                }
                className="w-full"
              >
                <Select.Option value={0}>Any Relevance</Select.Option>
                <Select.Option value={0.5}>50% or higher</Select.Option>
                <Select.Option value={0.7}>70% or higher</Select.Option>
                <Select.Option value={0.9}>90% or higher</Select.Option>
              </Select>
            </div>
          </Col>

          {/* Toggle Filters */}
          <Col xs={24} md={4}>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Include Anchors</span>
                <Switch
                  checked={filters.includeAnchors}
                  onChange={(checked) =>
                    handleFilterChange("includeAnchors", checked)
                  }
                  size="small"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Has PII</span>
                <Switch
                  checked={filters.hasPII}
                  onChange={(checked) => handleFilterChange("hasPII", checked)}
                  size="small"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Tagged</span>
                <Switch
                  checked={filters.hasTagged}
                  onChange={(checked) =>
                    handleFilterChange("hasTagged", checked)
                  }
                  size="small"
                />
              </div>
            </div>
          </Col>
        </Row>

        {/* Active Filters Display */}
        <div className="pt-2">
          <div className="flex flex-wrap gap-2">
            {filters.storageType !== "all" && (
              <Tag
                closable
                onClose={() => handleFilterChange("storageType", "all")}
              >
                Type: {filters.storageType}
              </Tag>
            )}
            {filters.dateRange && (
              <Tag
                closable
                onClose={() => handleFilterChange("dateRange", null)}
              >
                Date Range Applied
              </Tag>
            )}
            {filters.relevanceThreshold > 0 && (
              <Tag
                closable
                onClose={() => handleFilterChange("relevanceThreshold", 0)}
              >
                Min Relevance: {filters.relevanceThreshold * 100}%
              </Tag>
            )}
            {!filters.includeAnchors && (
              <Tag
                closable
                onClose={() => handleFilterChange("includeAnchors", true)}
              >
                Excluding Anchors
              </Tag>
            )}
            {filters.hasPII && (
              <Tag closable onClose={() => handleFilterChange("hasPII", false)}>
                Has PII
              </Tag>
            )}
            {filters.hasTagged && (
              <Tag
                closable
                onClose={() => handleFilterChange("hasTagged", false)}
              >
                Tagged Only
              </Tag>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
