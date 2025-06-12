"use client";

import { Button, Space, Divider } from "antd";
import {
  DeleteOutlined,
  ExportOutlined,
  TagOutlined,
  CheckOutlined,
} from "@ant-design/icons";

interface BulkOperationsProps {
  selectedCount: number;
  onBulkDelete: () => void;
  onBulkExport: () => void;
  onBulkTag: () => void;
  onDeselectAll: () => void;
}

export const BulkOperations: React.FC<BulkOperationsProps> = ({
  selectedCount,
  onBulkDelete,
  onBulkExport,
  onBulkTag,
  onDeselectAll,
}) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <span className="font-medium text-blue-700">
          {selectedCount} memories selected
        </span>

        <Divider type="vertical" />

        <Space>
          <Button icon={<DeleteOutlined />} danger onClick={onBulkDelete}>
            Delete Selected
          </Button>

          <Button icon={<ExportOutlined />} onClick={onBulkExport}>
            Export Selected
          </Button>

          <Button icon={<TagOutlined />} onClick={onBulkTag}>
            Add Tags
          </Button>
        </Space>
      </div>

      <Button type="text" onClick={onDeselectAll} icon={<CheckOutlined />}>
        Deselect All
      </Button>
    </div>
  );
};
