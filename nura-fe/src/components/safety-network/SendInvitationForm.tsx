"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  Input,
  Select,
  Button,
  Alert,
  Typography,
  Space,
  Steps,
  App,
} from "antd";
import {
  UserAddOutlined,
  MailOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons";
import { PermissionBuilder } from "./PermissionBuilder";
import { safetyInvitationsApi } from "@/services/apis/safety-invitations";

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface RelationshipType {
  value: string;
  label: string;
  description: string;
  suggested_permissions: string[];
}

interface SendInvitationFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const SendInvitationForm: React.FC<SendInvitationFormProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [relationshipTypes, setRelationshipTypes] = useState<
    RelationshipType[]
  >([]);
  const [selectedPermissions, setSelectedPermissions] = useState<
    Record<string, any>
  >({});
  const [selectedRelationship, setSelectedRelationship] =
    useState<RelationshipType | null>(null);
  const [formData, setFormData] = useState<{
    recipient_email?: string;
    relationship_type?: string;
    invitation_message?: string;
    priority_order?: number;
  }>({});
  const { message } = App.useApp();

  // Load relationship types
  useEffect(() => {
    const loadRelationshipTypes = async () => {
      try {
        const response = await fetch("/safety-invitations/relationship-types");
        const data = await response.json();

        if (data.success) {
          setRelationshipTypes(data.relationship_types || []);
        } else {
          setRelationshipTypes([]);
        }
      } catch (error) {
        console.error("Error loading relationship types:", error);
        message.error("Failed to load relationship options");
        setRelationshipTypes([]);
      }
    };

    loadRelationshipTypes();
  }, [message]);

  // Save current form data to state
  const saveFormData = () => {
    const currentValues = form.getFieldsValue();
    setFormData((prev) => ({ ...prev, ...currentValues }));
  };

  // Load form data from state
  const loadFormData = () => {
    form.setFieldsValue(formData);
  };

  // Handle relationship type change
  const handleRelationshipChange = (value: string) => {
    const relationship = relationshipTypes.find((r) => r.value === value);
    setSelectedRelationship(relationship || null);
    form.setFieldsValue({ relationship_type: value });
    // Save the change immediately
    setFormData((prev) => ({ ...prev, relationship_type: value }));
  };

  // Handle form submission
  const handleSubmit = async (values: any) => {
    setLoading(true);

    try {
      // Save any current form data before submission
      saveFormData();

      // Get the most current form values to ensure we have the latest data
      const currentFormValues = form.getFieldsValue();
      const finalFormData = { ...formData, ...currentFormValues };

      console.log("Final form data:", finalFormData);
      console.log("Selected permissions:", selectedPermissions);

      // Validate required fields using the final data
      if (!finalFormData.recipient_email) {
        message.error("Please enter a recipient email address");
        setCurrentStep(0);
        return;
      }

      if (!finalFormData.relationship_type) {
        message.error("Please select a relationship type");
        setCurrentStep(0);
        return;
      }

      const result = await safetyInvitationsApi.sendInvitation({
        recipient_email: finalFormData.recipient_email,
        relationship_type: finalFormData.relationship_type,
        invitation_message: finalFormData.invitation_message || "",
        requested_permissions: selectedPermissions,
        priority_order: finalFormData.priority_order,
      });

      if (result.success) {
        // Use the success message from backend if available
        const successMessage =
          result.message || "Invitation sent successfully! 🎉";
        message.success(successMessage);
        form.resetFields();
        setSelectedPermissions({});
        setCurrentStep(0);
        onSuccess?.();
      } else {
        // Backend returned error with user-friendly message
        message.error(result.message || "Failed to send invitation");
      }
    } catch (error: any) {
      console.error("Error sending invitation:", error);

      // Use user-friendly error messages from our improved backend
      let errorMessage = "Failed to send invitation";
      let errorType = "error"; // default to error, can be "warning" for less severe issues

      if (error.response?.data) {
        const errorData = error.response.data;

        // Check if backend sent user-friendly error
        if (errorData.user_friendly && errorData.message) {
          errorMessage = errorData.message;

          // Determine severity based on error type
          if (errorData.error === "PENDING_INVITATION_EXISTS") {
            errorType = "warning";
            errorMessage += " You can check your sent invitations below.";
          } else if (errorData.error === "ALREADY_IN_NETWORK") {
            errorType = "info";
            errorMessage +=
              " You can manage their permissions in your safety network.";
          } else if (errorData.error === "USER_NOT_FOUND") {
            errorType = "warning";
            errorMessage += " Please double-check the email address.";
          } else if (errorData.error === "VERIFICATION_REQUIRED") {
            errorType = "warning";
          }
        } else if (errorData.detail) {
          // Handle FastAPI validation errors
          if (Array.isArray(errorData.detail)) {
            // Multiple validation errors
            const errors = errorData.detail
              .map((err: any) => `${err.loc?.join(".")} - ${err.msg}`)
              .join(", ");
            errorMessage = `Validation errors: ${errors}`;
          } else if (typeof errorData.detail === "string") {
            // Single error message
            errorMessage = errorData.detail;
          } else {
            // Object error
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Display message with appropriate severity
      if (errorType === "warning") {
        message.warning(errorMessage);
      } else if (errorType === "info") {
        message.info(errorMessage);
      } else {
        message.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  // Check if current step is valid
  const isStepValid = (step: number): boolean => {
    switch (step) {
      case 0:
        const email =
          form.getFieldValue("recipient_email") || formData.recipient_email;
        const relationship =
          form.getFieldValue("relationship_type") || formData.relationship_type;
        console.log(
          "Step 0 validation - Email:",
          email,
          "Relationship:",
          relationship
        );
        return !!email && !!relationship;
      case 1:
        const hasPermissions =
          Object.keys(selectedPermissions).length > 0 ||
          Object.values(selectedPermissions.alert_preferences || {}).some(
            Boolean
          );
        console.log(
          "Step 1 validation - Has permissions:",
          hasPermissions,
          "Permissions:",
          selectedPermissions
        );
        return hasPermissions;
      case 2:
        return true; // Review step is always valid if we got here
      default:
        return false;
    }
  };

  // Generate summary for review step
  const generateSummary = () => {
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
    const enabledAlerts = Object.entries(
      selectedPermissions.alert_preferences || {}
    )
      .filter(([_, enabled]) => enabled)
      .map(([key, _]) => key);

    return {
      dataAccess: enabledData,
      alerts: enabledAlerts,
      total: enabledData.length + enabledAlerts.length,
    };
  };

  const steps = [
    {
      title: "Basic Info",
      description: "Who do you want to invite?",
      icon: <UserAddOutlined />,
    },
    {
      title: "Permissions",
      description: "What do you want to share?",
      icon: <MailOutlined />,
    },
    {
      title: "Review & Send",
      description: "Confirm your invitation",
      icon: <CheckCircleOutlined />,
    },
  ];

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <UserAddOutlined />
          <span>Invite Someone to Your Safety Network</span>
        </CardTitle>
        <div className="text-sm text-gray-600">
          Choose exactly what to share with complete control over your privacy
        </div>
      </CardHeader>

      <CardContent>
        {/* Progress Steps */}
        <Steps current={currentStep} className="mb-8">
          {steps.map((step, index) => (
            <Step
              key={index}
              title={step.title}
              description={step.description}
              icon={step.icon}
              status={
                index < currentStep
                  ? "finish"
                  : index === currentStep
                  ? "process"
                  : "wait"
              }
            />
          ))}
        </Steps>

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {/* Step 1: Basic Information */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <Alert
                message="Invitation Privacy"
                description="You have complete control over what this person can see. No information is shared automatically based on relationship type."
                type="info"
                showIcon
                className="mb-6"
              />

              <Form.Item
                name="recipient_email"
                label="Email Address"
                rules={[
                  { required: true, message: "Please enter an email address" },
                  {
                    type: "email",
                    message: "Please enter a valid email address",
                  },
                ]}
              >
                <Input
                  size="large"
                  placeholder="Enter the person's email address"
                  prefix={<MailOutlined />}
                  onChange={(e) => {
                    setFormData((prev) => ({
                      ...prev,
                      recipient_email: e.target.value,
                    }));
                  }}
                />
              </Form.Item>

              <Form.Item
                name="relationship_type"
                label="Relationship Type"
                help="This is just a label - it doesn't restrict what you can share"
                rules={[
                  {
                    required: true,
                    message: "Please select a relationship type",
                  },
                ]}
              >
                <Select
                  size="large"
                  placeholder="Select your relationship"
                  onChange={handleRelationshipChange}
                >
                  {relationshipTypes &&
                    relationshipTypes.map((type) => (
                      <Option key={type.value} value={type.value}>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-xs text-gray-500">
                            {type.description}
                          </div>
                        </div>
                      </Option>
                    ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="priority_order"
                label="Contact Priority"
                help="1 = highest priority (first to contact in emergency), higher numbers = lower priority"
              >
                <Input
                  type="number"
                  min={1}
                  max={100}
                  size="large"
                  placeholder="Enter priority number (1-100)"
                  value={formData.priority_order}
                  onChange={(e) => {
                    const value = e.target.value
                      ? parseInt(e.target.value)
                      : undefined;
                    setFormData((prev) => ({
                      ...prev,
                      priority_order: value,
                    }));
                  }}
                />
              </Form.Item>

              <Form.Item
                name="invitation_message"
                label="Personal Message (Optional)"
                help="Add a personal note to your invitation"
              >
                <TextArea
                  rows={3}
                  placeholder="Hi! I'd like to add you to my safety network..."
                  maxLength={500}
                  showCount
                  onChange={(e) => {
                    setFormData((prev) => ({
                      ...prev,
                      invitation_message: e.target.value,
                    }));
                  }}
                />
              </Form.Item>

              {selectedRelationship &&
                selectedRelationship.suggested_permissions && (
                  <Alert
                    message={`Common permissions for ${selectedRelationship.label}:`}
                    description={
                      <div className="flex flex-wrap gap-1 mt-2">
                        {Array.isArray(
                          selectedRelationship.suggested_permissions
                        ) &&
                          selectedRelationship.suggested_permissions.map(
                            (perm) => (
                              <span
                                key={perm}
                                className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs"
                              >
                                {perm}
                              </span>
                            )
                          )}
                      </div>
                    }
                    type="info"
                    showIcon={false}
                    className="bg-blue-50 border-blue-200"
                  />
                )}

              <div className="flex justify-end">
                <Button
                  type="primary"
                  size="large"
                  disabled={!isStepValid(0)}
                  onClick={() => {
                    saveFormData();
                    setCurrentStep(1);
                  }}
                  icon={<ArrowRightOutlined />}
                  iconPosition="end"
                >
                  Choose Permissions
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Permission Selection */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <PermissionBuilder
                selectedPermissions={selectedPermissions}
                onPermissionsChange={setSelectedPermissions}
                relationshipType={selectedRelationship?.label}
                suggestedPermissions={
                  selectedRelationship?.suggested_permissions
                }
              />

              <div className="flex justify-between">
                <Button
                  size="large"
                  onClick={() => {
                    loadFormData();
                    setCurrentStep(0);
                  }}
                  icon={<ArrowLeftOutlined />}
                >
                  Back
                </Button>
                <Button
                  type="primary"
                  size="large"
                  disabled={!isStepValid(1)}
                  onClick={() => {
                    saveFormData();
                    setCurrentStep(2);
                  }}
                  icon={<ArrowRightOutlined />}
                  iconPosition="end"
                >
                  Review & Send
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Review and Confirm */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <Alert
                message="Review Your Invitation"
                description="Please review the details below before sending your invitation."
                type="warning"
                showIcon
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Invitation Details */}
                <Card title="Invitation Details">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text type="secondary">Recipient:</Text>
                      <div className="font-medium">
                        {formData.recipient_email ||
                          form.getFieldValue("recipient_email")}
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Relationship:</Text>
                      <div className="font-medium">
                        {selectedRelationship?.label}
                      </div>
                    </div>
                    {(formData.priority_order ||
                      form.getFieldValue("priority_order")) && (
                      <div>
                        <Text type="secondary">Priority Level:</Text>
                        <div className="font-medium">
                          Priority{" "}
                          {formData.priority_order ||
                            form.getFieldValue("priority_order")}
                          {(formData.priority_order ||
                            form.getFieldValue("priority_order")) === 1 &&
                            " (Highest Priority)"}
                        </div>
                      </div>
                    )}
                    {(formData.invitation_message ||
                      form.getFieldValue("invitation_message")) && (
                      <div>
                        <Text type="secondary">Message:</Text>
                        <div className="font-medium italic">
                          "
                          {formData.invitation_message ||
                            form.getFieldValue("invitation_message")}
                          "
                        </div>
                      </div>
                    )}
                  </Space>
                </Card>

                {/* Permission Summary */}
                <Card title="What You're Sharing">
                  {(() => {
                    const summary = generateSummary();
                    return (
                      <Space direction="vertical" className="w-full">
                        <div>
                          <Text strong>{summary.total} total permissions</Text>
                        </div>

                        {summary.dataAccess.length > 0 && (
                          <div>
                            <Text type="secondary">
                              Data Access ({summary.dataAccess.length}):
                            </Text>
                            <ul className="list-disc list-inside text-sm">
                              {summary.dataAccess.map((perm) => (
                                <li key={perm} className="text-gray-600">
                                  {perm
                                    .replace("can_see_", "")
                                    .replace("_", " ")}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {summary.alerts.length > 0 && (
                          <div>
                            <Text type="secondary">
                              Notifications ({summary.alerts.length}):
                            </Text>
                            <ul className="list-disc list-inside text-sm">
                              {summary.alerts.map((alert) => (
                                <li key={alert} className="text-gray-600">
                                  {alert.replace("_", " ")}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {summary.total === 0 && (
                          <Text type="secondary" italic>
                            No permissions selected - they'll only see basic
                            profile info
                          </Text>
                        )}
                      </Space>
                    );
                  })()}
                </Card>
              </div>

              <Alert
                message="Privacy Reminder"
                description="The recipient can see exactly what permissions you're requesting when they receive the invitation. They can also modify these permissions when accepting."
                type="success"
                showIcon
              />

              <div className="flex justify-between">
                <Button
                  size="large"
                  onClick={() => {
                    loadFormData();
                    setCurrentStep(1);
                  }}
                  icon={<ArrowLeftOutlined />}
                >
                  Back to Permissions
                </Button>
                <Space>
                  <Button size="large" onClick={onCancel}>
                    Cancel
                  </Button>
                  <Button
                    type="primary"
                    size="large"
                    htmlType="submit"
                    loading={loading}
                    icon={<MailOutlined />}
                  >
                    Send Invitation
                  </Button>
                </Space>
              </div>
            </div>
          )}
        </Form>
      </CardContent>
    </Card>
  );
};
