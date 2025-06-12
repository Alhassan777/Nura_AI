"use client";

import React, { useState } from "react";
import {
  Card,
  Button,
  List,
  Typography,
  Tag,
  Progress,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Space,
  Divider,
} from "antd";
import {
  Target,
  Plus,
  CheckCircle,
  Clock,
  User,
  Calendar,
  Edit3,
  Trash2,
  TrendingUp,
  Heart,
  Brain,
} from "lucide-react";
import {
  useActionPlans,
  useCreateActionPlan,
  useUpdateActionPlan,
  useDeleteActionPlan,
} from "@/services/hooks/use-action-plans";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ActionPlan {
  id: string;
  title: string;
  type: "therapeutic_emotional" | "personal_achievement";
  description: string;
  steps: ActionStep[];
  created_at: string;
  due_date?: string;
  priority: "low" | "medium" | "high";
  status: "active" | "completed" | "paused";
  progress: number;
  tags: string[];
}

interface ActionStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  due_date?: string;
  notes?: string;
}

export default function ActionPlansPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<ActionPlan | null>(null);
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterType, setFilterType] = useState("all");

  const { data: actionPlans, isLoading } = useActionPlans();
  const { mutate: createPlan, isPending: isCreating } = useCreateActionPlan();
  const { mutate: updatePlan, isPending: isUpdating } = useUpdateActionPlan();
  const { mutate: deletePlan, isPending: isDeleting } = useDeleteActionPlan();

  const [form] = Form.useForm();

  const filteredPlans =
    actionPlans?.filter((plan: ActionPlan) => {
      const statusMatch =
        filterStatus === "all" || plan.status === filterStatus;
      const typeMatch = filterType === "all" || plan.type === filterType;
      return statusMatch && typeMatch;
    }) || [];

  const handleCreatePlan = (values: any) => {
    const newPlan = {
      ...values,
      steps: values.steps || [],
      progress: 0,
      status: "active",
      created_at: new Date().toISOString(),
    };
    createPlan(newPlan);
    setShowCreateModal(false);
    form.resetFields();
  };

  const handleUpdatePlan = (planId: string, updates: Partial<ActionPlan>) => {
    updatePlan({ id: planId, ...updates });
  };

  const handleDeletePlan = (planId: string) => {
    Modal.confirm({
      title: "Delete Action Plan",
      content: "Are you sure you want to delete this action plan?",
      onOk: () => deletePlan(planId),
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "red";
      case "medium":
        return "orange";
      case "low":
        return "green";
      default:
        return "default";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "green";
      case "active":
        return "blue";
      case "paused":
        return "orange";
      default:
        return "default";
    }
  };

  const getTypeIcon = (type: string) => {
    return type === "therapeutic_emotional" ? (
      <Heart className="h-4 w-4" />
    ) : (
      <TrendingUp className="h-4 w-4" />
    );
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Target className="h-8 w-8 text-green-600" />
          <Title level={2} className="!mb-0">
            Action Plans
          </Title>
        </div>
        <Button
          type="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Create New Plan
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {actionPlans?.length || 0}
            </div>
            <div className="text-sm text-gray-500">Total Plans</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {actionPlans?.filter((p: ActionPlan) => p.status === "active")
                .length || 0}
            </div>
            <div className="text-sm text-gray-500">Active Plans</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {actionPlans?.filter((p: ActionPlan) => p.status === "completed")
                .length || 0}
            </div>
            <div className="text-sm text-gray-500">Completed</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {Math.round(
                actionPlans?.reduce(
                  (sum: number, p: ActionPlan) => sum + p.progress,
                  0
                ) / (actionPlans?.length || 1)
              ) || 0}
              %
            </div>
            <div className="text-sm text-gray-500">Avg Progress</div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <div>
            <Text strong>Status:</Text>
            <Select
              value={filterStatus}
              onChange={setFilterStatus}
              className="ml-2 w-32"
            >
              <Option value="all">All</Option>
              <Option value="active">Active</Option>
              <Option value="completed">Completed</Option>
              <Option value="paused">Paused</Option>
            </Select>
          </div>
          <div>
            <Text strong>Type:</Text>
            <Select
              value={filterType}
              onChange={setFilterType}
              className="ml-2 w-40"
            >
              <Option value="all">All Types</Option>
              <Option value="therapeutic_emotional">Emotional Wellness</Option>
              <Option value="personal_achievement">Personal Goals</Option>
            </Select>
          </div>
        </div>
      </Card>

      {/* Action Plans List */}
      <Card>
        {isLoading ? (
          <div className="text-center py-8">Loading action plans...</div>
        ) : filteredPlans.length > 0 ? (
          <List
            dataSource={filteredPlans}
            renderItem={(plan: ActionPlan) => (
              <List.Item
                actions={[
                  <Button
                    key="edit"
                    type="text"
                    icon={<Edit3 className="h-4 w-4" />}
                    onClick={() => setEditingPlan(plan)}
                  >
                    Edit
                  </Button>,
                  <Button
                    key="delete"
                    type="text"
                    danger
                    icon={<Trash2 className="h-4 w-4" />}
                    onClick={() => handleDeletePlan(plan.id)}
                  >
                    Delete
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <div className="p-2 bg-green-100 rounded-full">
                      {getTypeIcon(plan.type)}
                    </div>
                  }
                  title={
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{plan.title}</span>
                      <div className="flex items-center space-x-2">
                        <Tag color={getPriorityColor(plan.priority)}>
                          {plan.priority.toUpperCase()}
                        </Tag>
                        <Tag color={getStatusColor(plan.status)}>
                          {plan.status.toUpperCase()}
                        </Tag>
                      </div>
                    </div>
                  }
                  description={
                    <div className="space-y-2">
                      <p className="text-gray-600 text-sm">
                        {plan.description}
                      </p>

                      <div className="flex items-center space-x-4">
                        <Progress
                          percent={plan.progress}
                          size="small"
                          className="flex-1"
                          strokeColor={{
                            "0%": "#108ee9",
                            "100%": "#87d068",
                          }}
                        />
                        <Text className="text-xs text-gray-500">
                          {plan.steps.filter((s) => s.completed).length} /{" "}
                          {plan.steps.length} steps
                        </Text>
                      </div>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          Created{" "}
                          {new Date(plan.created_at).toLocaleDateString()}
                        </span>
                        {plan.due_date && (
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            Due {new Date(plan.due_date).toLocaleDateString()}
                          </span>
                        )}
                        <span>{plan.steps.length} steps</span>
                      </div>

                      {plan.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {plan.tags.map((tag, index) => (
                            <Tag key={index}>{tag}</Tag>
                          ))}
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Target className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <Text>No action plans found.</Text>
            <br />
            <Text type="secondary">
              Create your first action plan to start tracking your goals.
            </Text>
          </div>
        )}
      </Card>

      {/* Create/Edit Action Plan Modal */}
      <Modal
        title={editingPlan ? "Edit Action Plan" : "Create New Action Plan"}
        open={showCreateModal || !!editingPlan}
        onCancel={() => {
          setShowCreateModal(false);
          setEditingPlan(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={
            editingPlan
              ? (values) => {
                  handleUpdatePlan(editingPlan.id, values);
                  setEditingPlan(null);
                  form.resetFields();
                }
              : handleCreatePlan
          }
          initialValues={
            editingPlan || {
              type: "personal_achievement",
              priority: "medium",
            }
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="title"
              label="Plan Title"
              rules={[{ required: true, message: "Please enter a title" }]}
            >
              <Input placeholder="e.g., Improve Daily Meditation Practice" />
            </Form.Item>

            <Form.Item
              name="type"
              label="Plan Type"
              rules={[{ required: true }]}
            >
              <Select>
                <Option value="therapeutic_emotional">
                  <Space>
                    <Heart className="h-4 w-4" />
                    Emotional Wellness
                  </Space>
                </Option>
                <Option value="personal_achievement">
                  <Space>
                    <TrendingUp className="h-4 w-4" />
                    Personal Goals
                  </Space>
                </Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="priority"
              label="Priority"
              rules={[{ required: true }]}
            >
              <Select>
                <Option value="low">Low</Option>
                <Option value="medium">Medium</Option>
                <Option value="high">High</Option>
              </Select>
            </Form.Item>

            <Form.Item name="due_date" label="Due Date (Optional)">
              <DatePicker className="w-full" />
            </Form.Item>
          </div>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: "Please enter a description" }]}
          >
            <TextArea
              rows={3}
              placeholder="Describe what you want to achieve and why it's important to you..."
            />
          </Form.Item>

          <Form.Item name="tags" label="Tags (Optional)">
            <Select
              mode="tags"
              placeholder="Add tags to categorize your plan"
              tokenSeparators={[","]}
            />
          </Form.Item>

          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => {
                setShowCreateModal(false);
                setEditingPlan(null);
                form.resetFields();
              }}
            >
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={isCreating || isUpdating}
            >
              {editingPlan ? "Update Plan" : "Create Plan"}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
