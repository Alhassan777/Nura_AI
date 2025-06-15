"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Switch,
  Alert,
  Tag,
  Collapse,
  Space,
  Typography,
  Button,
  Tooltip,
  Divider,
} from "antd";
import {
  SafetyCertificateOutlined,
  HeartOutlined,
  BellOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
} from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;

interface Permission {
  key: string;
  name: string;
  description: string;
  privacy_level: "high" | "medium" | "low";
  category: "emergency" | "wellness" | "alerts";
}

interface PermissionCategory {
  name: string;
  description: string;
  privacy_note: string;
}

interface PermissionBuilderProps {
  selectedPermissions: Record<string, any>;
  onPermissionsChange: (permissions: Record<string, any>) => void;
  relationshipType?: string;
  suggestedPermissions?: string[];
  className?: string;
}

export const PermissionBuilder: React.FC<PermissionBuilderProps> = ({
  selectedPermissions,
  onPermissionsChange,
  relationshipType,
  suggestedPermissions = [],
  className = "",
}) => {
  const [availablePermissions, setAvailablePermissions] = useState<
    Record<string, Permission>
  >({});
  const [categories, setCategories] = useState<
    Record<string, PermissionCategory>
  >({});
  const [loading, setLoading] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Load available permissions from backend
  useEffect(() => {
    const loadPermissions = async () => {
      try {
        const response = await fetch(
          "/safety-invitations/permissions/available"
        );
        const data = await response.json();

        if (data.success) {
          setAvailablePermissions(data.permissions);
          setCategories(data.categories);
        }
      } catch (error) {
        console.error("Error loading permissions:", error);
      } finally {
        setLoading(false);
      }
    };

    loadPermissions();
  }, []);

  // Handle permission toggle
  const handlePermissionToggle = (
    permissionKey: string,
    permissionCategory: string,
    enabled: boolean
  ) => {
    const newPermissions = { ...selectedPermissions };

    if (permissionCategory === "alerts") {
      // Handle alert preferences
      if (!newPermissions.alert_preferences) {
        newPermissions.alert_preferences = {};
      }
      newPermissions.alert_preferences[permissionKey] = enabled;
    } else {
      // Handle direct permissions
      newPermissions[permissionKey] = enabled;
    }

    onPermissionsChange(newPermissions);
  };

  // Check if permission is enabled
  const isPermissionEnabled = (
    permissionKey: string,
    permissionCategory: string
  ): boolean => {
    if (permissionCategory === "alerts") {
      return selectedPermissions.alert_preferences?.[permissionKey] || false;
    }
    return selectedPermissions[permissionKey] || false;
  };

  // Apply suggested permissions for relationship type
  const applySuggested = () => {
    const newPermissions = { ...selectedPermissions };

    suggestedPermissions.forEach((suggestionKey) => {
      const permission = Object.values(availablePermissions).find(
        (p) =>
          suggestionKey === p.key ||
          suggestionKey ===
            Object.keys(availablePermissions).find(
              (k) => availablePermissions[k].key === suggestionKey
            )
      );

      if (permission) {
        if (permission.category === "alerts") {
          if (!newPermissions.alert_preferences) {
            newPermissions.alert_preferences = {};
          }
          newPermissions.alert_preferences[permission.key] = true;
        } else {
          newPermissions[permission.key] = true;
        }
      }
    });

    onPermissionsChange(newPermissions);
  };

  // Clear all permissions
  const clearAll = () => {
    onPermissionsChange({
      alert_preferences: {},
    });
  };

  // Get privacy level indicator
  const getPrivacyLevelColor = (level: string) => {
    switch (level) {
      case "high":
        return "red";
      case "medium":
        return "orange";
      case "low":
        return "green";
      default:
        return "blue";
    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "emergency":
        return <SafetyCertificateOutlined />;
      case "wellness":
        return <HeartOutlined />;
      case "alerts":
        return <BellOutlined />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  // Calculate permission summary
  const getPermissionSummary = () => {
    const dataPermissions = [
      "can_see_location",
      "can_see_mood",
      "can_see_activities",
      "can_see_goals",
      "can_see_status",
    ];
    const enabledData = dataPermissions.filter(
      (key) => selectedPermissions[key]
    );
    const enabledAlerts = Object.values(
      selectedPermissions.alert_preferences || {}
    ).filter(Boolean).length;

    return {
      dataCount: enabledData.length,
      alertCount: enabledAlerts,
      total: enabledData.length + enabledAlerts,
    };
  };

  const summary = getPermissionSummary();

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <Text>Loading permission options...</Text>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <EyeOutlined />
            <span>Choose What to Share</span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              size="small"
              onClick={() => setShowAdvanced(!showAdvanced)}
              icon={showAdvanced ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            >
              {showAdvanced ? "Simple" : "Advanced"}
            </Button>
          </div>
        </CardTitle>
        <div className="text-sm text-gray-600">
          You have complete control over what information this person can access
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Permission Summary */}
        <Alert
          message={
            <div className="flex items-center justify-between">
              <span>
                <strong>{summary.total}</strong> permissions selected
                {summary.total > 0 && (
                  <span className="text-gray-600 ml-2">
                    ({summary.dataCount} data access, {summary.alertCount}{" "}
                    notifications)
                  </span>
                )}
              </span>
              <div className="flex space-x-2">
                {suggestedPermissions.length > 0 && (
                  <Button size="small" type="link" onClick={applySuggested}>
                    Apply Suggested for {relationshipType}
                  </Button>
                )}
                {summary.total > 0 && (
                  <Button size="small" type="link" danger onClick={clearAll}>
                    Clear All
                  </Button>
                )}
              </div>
            </div>
          }
          type="info"
          showIcon={false}
        />

        {/* Quick Suggestions */}
        {suggestedPermissions.length > 0 && (
          <Alert
            message={
              <div>
                <Text strong>Suggested for {relationshipType}:</Text>
                <div className="mt-2 flex flex-wrap gap-1">
                  {suggestedPermissions.map((suggestionKey) => {
                    const permission = Object.values(availablePermissions).find(
                      (p) =>
                        suggestionKey === p.key ||
                        suggestionKey ===
                          Object.keys(availablePermissions).find(
                            (k) => availablePermissions[k].key === suggestionKey
                          )
                    );
                    return permission ? (
                      <Tag key={suggestionKey} color="blue" className="text-xs">
                        {permission.name}
                      </Tag>
                    ) : null;
                  })}
                </div>
              </div>
            }
            type="warning"
            showIcon={false}
            className="bg-blue-50 border-blue-200"
          />
        )}

        {/* Permission Categories */}
        <Collapse
          defaultActiveKey={["emergency", "wellness", "alerts"]}
          className="bg-white"
          items={Object.entries(categories)
            .map(([categoryKey, category]) => {
              const categoryPermissions = Object.entries(
                availablePermissions
              ).filter(
                ([_, permission]) => permission.category === categoryKey
              );

              if (categoryPermissions.length === 0) return null;

              return {
                key: categoryKey,
                label: (
                  <div className="flex items-center space-x-3">
                    {getCategoryIcon(categoryKey)}
                    <div>
                      <div className="font-medium">{category.name}</div>
                      <div className="text-xs text-gray-500">
                        {category.description}
                      </div>
                    </div>
                  </div>
                ),
                extra: (
                  <Tag
                    color={
                      categoryKey === "emergency"
                        ? "red"
                        : categoryKey === "wellness"
                        ? "orange"
                        : "blue"
                    }
                  >
                    {
                      categoryPermissions.filter(([permKey, perm]) =>
                        isPermissionEnabled(perm.key, perm.category)
                      ).length
                    }{" "}
                    / {categoryPermissions.length}
                  </Tag>
                ),
                children: (
                  <div className="space-y-4">
                    <Alert
                      message={category.privacy_note}
                      type="info"
                      showIcon={false}
                      className="mb-4"
                    />

                    {categoryPermissions.map(([permissionKey, permission]) => (
                      <div
                        key={permissionKey}
                        className="flex items-start justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex-1 mr-4">
                          <div className="flex items-center space-x-2">
                            <Text strong>{permission.name}</Text>
                            <Tag
                              color={getPrivacyLevelColor(
                                permission.privacy_level
                              )}
                            >
                              {permission.privacy_level} privacy
                            </Tag>
                          </div>
                          <Paragraph className="text-sm text-gray-600 mb-0 mt-1">
                            {permission.description}
                          </Paragraph>
                        </div>
                        <div className="flex items-center">
                          <Switch
                            checked={isPermissionEnabled(
                              permission.key,
                              permission.category
                            )}
                            onChange={(checked) =>
                              handlePermissionToggle(
                                permission.key,
                                permission.category,
                                checked
                              )
                            }
                            checkedChildren="Yes"
                            unCheckedChildren="No"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ),
              };
            })
            .filter((item): item is NonNullable<typeof item> => item !== null)}
        />

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="border-t pt-4">
            <Title level={5}>Advanced Options</Title>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <Text strong>Emergency Contact</Text>
                  <div className="text-sm text-gray-600">
                    Allow this person to be contacted during mental health
                    crises
                  </div>
                </div>
                <Switch
                  checked={selectedPermissions.is_emergency_contact || false}
                  onChange={(checked) =>
                    onPermissionsChange({
                      ...selectedPermissions,
                      is_emergency_contact: checked,
                    })
                  }
                />
              </div>
            </div>
          </div>
        )}

        {/* Privacy Notice */}
        <Alert
          message="Privacy Control"
          description="You can modify these permissions anytime after accepting the invitation. This person will only see what you explicitly allow them to see."
          type="success"
          showIcon
        />
      </CardContent>
    </Card>
  );
};
