import { Space, Spin, Typography } from "antd";
import { Alert as AntdAlert } from "antd";
import { AlertTriangle, CheckCircle, Loader2, XCircle } from "lucide-react";
import { useHealthStatus } from "@/services/hooks";

const { Title, Text } = Typography;

const ServerHealthStatus = ({ userId }: { userId: string }) => {
  const { data: healthStatus, isLoading, error } = useHealthStatus();

  console.log(healthStatus);

  const getHealthStatusIcon = () => {
    if (isLoading)
      return (
        <Spin
          indicator={<Loader2 className="h-4 w-4 animate-spin" />}
          size="small"
        />
      );
    switch (healthStatus.status) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div>
      <Title level={2}>Nura Memory System Test Chat</Title>
      <Space align="center">
        {getHealthStatusIcon()}
        <Text type="secondary">
          Service Status: {healthStatus?.status || "checking..."}
        </Text>
        <Text type="secondary" style={{ fontSize: "12px" }}>
          User ID: {userId}
        </Text>
      </Space>
      {error && (
        <AntdAlert
          message={error.message}
          type="error"
          showIcon
          style={{ marginTop: "8px" }}
        />
      )}
    </div>
  );
};

export default ServerHealthStatus;
