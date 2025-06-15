"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
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
  message,
  Tooltip,
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
  ArrowRight,
  ListTodo,
  ExternalLink,
  Edit,
} from "lucide-react";
import {
  useActionPlans,
  useCreateActionPlan,
  useUpdateActionPlan,
  useDeleteActionPlan,
  ActionPlan,
} from "@/services/hooks/use-action-plans";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function ActionPlansPage() {
  const router = useRouter();
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
      const typeMatch = filterType === "all" || plan.plan_type === filterType;
      return statusMatch && typeMatch;
    }) || [];

  const handleCreatePlan = (values: any) => {
    const newPlan = {
      ...values,
      steps: values.steps || [],
      status: "active" as const,
      tags: values.tags || [],
      due_date: values.due_date?.toISOString(),
    };

    createPlan(newPlan, {
      onSuccess: () => {
        message.success("Action plan created successfully!");
        setShowCreateModal(false);
        form.resetFields();
      },
      onError: (error) => {
        message.error("Failed to create action plan. Please try again.");
        console.error("Create plan error:", error);
      },
    });
  };

  const handleUpdatePlan = (planId: string, updates: Partial<ActionPlan>) => {
    updatePlan(
      { id: planId, ...updates },
      {
        onSuccess: () => {
          message.success("Action plan updated successfully!");
          setEditingPlan(null);
          form.resetFields();
        },
        onError: (error) => {
          message.error("Failed to update action plan. Please try again.");
          console.error("Update plan error:", error);
        },
      }
    );
  };

  const handleDeletePlan = (planId: string) => {
    Modal.confirm({
      title: "Delete Action Plan",
      content:
        "Are you sure you want to delete this action plan? This action cannot be undone.",
      okText: "Delete",
      okType: "danger",
      onOk: () => {
        deletePlan(planId, {
          onSuccess: () => {
            message.success("Action plan deleted successfully!");
          },
          onError: (error) => {
            message.error("Failed to delete action plan. Please try again.");
            console.error("Delete plan error:", error);
          },
        });
      },
    });
  };

  const handlePlanClick = (planId: string) => {
    router.push(`/action-plans/${planId}`);
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

  const activeCount =
    actionPlans?.filter((p) => p.status === "active").length || 0;
  const completedCount =
    actionPlans?.filter((p) => p.status === "completed").length || 0;
  const totalPlans = actionPlans?.length || 0;
  const avgProgress =
    totalPlans > 0
      ? Math.round(
          (actionPlans || []).reduce(
            (sum, p) => sum + p.progress_percentage,
            0
          ) / totalPlans
        )
      : 0;

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
        <Card className="text-center">
          <div className="text-2xl font-bold text-blue-600">{totalPlans}</div>
          <div className="text-sm text-gray-500">Total Plans</div>
        </Card>
        <Card className="text-center">
          <div className="text-2xl font-bold text-green-600">{activeCount}</div>
          <div className="text-sm text-gray-500">Active Plans</div>
        </Card>
        <Card className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {completedCount}
          </div>
          <div className="text-sm text-gray-500">Completed</div>
        </Card>
        <Card className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {avgProgress}%
          </div>
          <div className="text-sm text-gray-500">Avg Progress</div>
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
              <Option value="hybrid">Hybrid</Option>
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
            renderItem={(plan: ActionPlan) => {
              const completedSteps = plan.steps.filter((step) =>
                step.subtasks && step.subtasks.length > 0
                  ? step.subtasks.every((st) => st.completed)
                  : step.completed
              ).length;

              return (
                <List.Item
                  className="cursor-pointer hover:bg-gray-50 transition-colors duration-200 rounded-lg p-4 border border-transparent hover:border-gray-200"
                  onClick={() => handlePlanClick(plan.id)}
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      icon={<ExternalLink className="h-4 w-4" />}
                      onClick={() => router.push(`/action-plans/${plan.id}`)}
                    >
                      View Details
                    </Button>,
                    <Button
                      key="edit"
                      type="link"
                      icon={<Edit className="h-4 w-4" />}
                      onClick={() => {
                        setEditingPlan(plan);
                      }}
                    >
                      Edit
                    </Button>,
                    <Button
                      key="delete"
                      type="link"
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
                      <div className="p-3 bg-green-100 rounded-full">
                        {getTypeIcon(plan.plan_type)}
                      </div>
                    }
                    title={
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-lg">
                            {plan.title}
                          </span>
                          <Tooltip
                            title={`${completedSteps}/${plan.steps.length} tasks completed`}
                          >
                            <div className="flex items-center gap-1 text-sm text-gray-500">
                              <ListTodo className="h-3 w-3" />
                              <span>{plan.steps.length}</span>
                            </div>
                          </Tooltip>
                        </div>
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
                      <div className="space-y-3">
                        <p className="text-gray-600 text-sm">
                          {plan.description}
                        </p>

                        <div className="flex items-center space-x-4">
                          <Progress
                            percent={plan.progress_percentage}
                            size="small"
                            className="flex-1"
                            strokeColor={{
                              "0%": "#108ee9",
                              "100%": "#87d068",
                            }}
                            format={(percent) => `${percent}%`}
                          />
                          <Text className="text-xs text-gray-500 whitespace-nowrap">
                            {completedSteps} / {plan.steps.length} steps
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
                          {plan.steps.length > 0 && (
                            <span className="flex items-center">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              {completedSteps} completed
                            </span>
                          )}
                        </div>

                        {plan.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {plan.tags.map((tag, index) => (
                              <Tag key={index} className="text-xs">
                                {tag}
                              </Tag>
                            ))}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Target className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <Title level={4} className="text-gray-400">
              No action plans found
            </Title>
            <Text type="secondary" className="block mb-4">
              Create your first action plan to start tracking your goals and
              building positive habits.
            </Text>
            <Button
              type="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setShowCreateModal(true)}
            >
              Create Your First Plan
            </Button>
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
              ? (values) => handleUpdatePlan(editingPlan.id, values)
              : handleCreatePlan
          }
          initialValues={
            editingPlan || {
              plan_type: "personal_achievement",
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
              name="plan_type"
              label="Plan Type"
              rules={[{ required: true }]}
            >
              <Select placeholder="Select plan type">
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
                <Option value="hybrid">
                  <Space>
                    <Brain className="h-4 w-4" />
                    Hybrid Plan
                  </Space>
                </Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="priority"
              label="Priority"
              rules={[{ required: true }]}
            >
              <Select placeholder="Select priority">
                <Option value="low">Low Priority</Option>
                <Option value="medium">Medium Priority</Option>
                <Option value="high">High Priority</Option>
              </Select>
            </Form.Item>

            <Form.Item name="due_date" label="Due Date (Optional)">
              <DatePicker className="w-full" placeholder="Select due date" />
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
              placeholder="Add tags to categorize your plan (press Enter to add)"
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
