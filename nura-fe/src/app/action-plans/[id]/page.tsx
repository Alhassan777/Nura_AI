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
  Checkbox,
  Divider,
  Tooltip,
  message,
  Collapse,
  Empty,
} from "antd";
import {
  ArrowLeft,
  Target,
  Plus,
  CheckCircle,
  Clock,
  Calendar,
  Edit3,
  Trash2,
  TrendingUp,
  Heart,
  ListTodo,
  ChevronRight,
  ChevronDown,
  NotebookPen,
} from "lucide-react";
import {
  useActionPlan,
  useUpdateActionPlan,
  useUpdateStepStatus,
  useUpdateSubtaskStatus,
  useAddStep,
  useAddSubtask,
  ActionStep,
  ActionSubtask,
} from "@/services/hooks/use-action-plans";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;

interface ActionPlanDetailPageProps {
  params: {
    id: string;
  };
}

export default function ActionPlanDetailPage({
  params,
}: ActionPlanDetailPageProps) {
  const router = useRouter();
  const [showAddStepModal, setShowAddStepModal] = useState(false);
  const [showAddSubtaskModal, setShowAddSubtaskModal] = useState(false);
  const [editingStep, setEditingStep] = useState<ActionStep | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const { data: actionPlan, isLoading } = useActionPlan(params.id);
  const { mutate: updatePlan } = useUpdateActionPlan();
  const { mutate: updateStepStatus } = useUpdateStepStatus();
  const { mutate: updateSubtaskStatus } = useUpdateSubtaskStatus();
  const { mutate: addStep } = useAddStep();
  const { mutate: addSubtask } = useAddSubtask();

  const [stepForm] = Form.useForm();
  const [subtaskForm] = Form.useForm();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">Loading action plan...</div>
      </div>
    );
  }

  if (!actionPlan) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">
          <Empty description="Action plan not found">
            <Button type="primary" onClick={() => router.push("/action-plans")}>
              Back to Action Plans
            </Button>
          </Empty>
        </div>
      </div>
    );
  }

  const handleStepStatusChange = (stepId: string, completed: boolean) => {
    updateStepStatus(
      { planId: params.id, stepId, completed },
      {
        onSuccess: () => {
          message.success(
            completed ? "Step completed!" : "Step marked as incomplete"
          );
        },
      }
    );
  };

  const handleSubtaskStatusChange = (
    stepId: string,
    subtaskId: string,
    completed: boolean
  ) => {
    updateSubtaskStatus(
      { planId: params.id, stepId, subtaskId, completed },
      {
        onSuccess: () => {
          message.success(
            completed ? "Subtask completed!" : "Subtask marked as incomplete"
          );
        },
      }
    );
  };

  const handleAddStep = (values: any) => {
    const newStep = {
      title: values.title,
      description: values.description || "",
      completed: false,
      due_date: values.due_date?.toISOString(),
    };

    addStep(
      { planId: params.id, step: newStep },
      {
        onSuccess: () => {
          message.success("Step added successfully!");
          setShowAddStepModal(false);
          stepForm.resetFields();
        },
      }
    );
  };

  const handleAddSubtask = (values: any) => {
    if (!selectedStepId) return;

    const newSubtask = {
      title: values.title,
      description: values.description,
      completed: false,
      due_date: values.due_date?.toISOString(),
    };

    addSubtask(
      { planId: params.id, stepId: selectedStepId, subtask: newSubtask },
      {
        onSuccess: () => {
          message.success("Subtask added successfully!");
          setShowAddSubtaskModal(false);
          setSelectedStepId(null);
          subtaskForm.resetFields();
        },
      }
    );
  };

  const toggleStepExpansion = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getTypeIcon = (type: string) => {
    return type === "therapeutic_emotional" ? (
      <Heart className="h-5 w-5 text-pink-500" />
    ) : (
      <TrendingUp className="h-5 w-5 text-blue-500" />
    );
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

  const completedSteps = actionPlan.steps.filter((step) =>
    step.subtasks.length > 0
      ? step.subtasks.every((st) => st.completed)
      : step.completed
  ).length;

  const totalSteps = actionPlan.steps.length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            type="text"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => router.push("/action-plans")}
          >
            Back
          </Button>
          <div className="flex items-center gap-3">
            {getTypeIcon(actionPlan.plan_type)}
            <Title level={2} className="!mb-0">
              {actionPlan.title}
            </Title>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Tag color={getPriorityColor(actionPlan.priority)}>
            {actionPlan.priority.toUpperCase()}
          </Tag>
          <Tag color={getStatusColor(actionPlan.status)}>
            {actionPlan.status.toUpperCase()}
          </Tag>
        </div>
      </div>

      {/* Plan Overview */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <Paragraph className="text-gray-600 mb-4">
              {actionPlan.description}
            </Paragraph>

            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Created {new Date(actionPlan.created_at).toLocaleDateString()}
              </span>
              {actionPlan.due_date && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  Due {new Date(actionPlan.due_date).toLocaleDateString()}
                </span>
              )}
              <span>{totalSteps} steps</span>
            </div>

            {actionPlan.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {actionPlan.tags.map((tag, index) => (
                  <Tag key={index}>{tag}</Tag>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {actionPlan.progress_percentage}%
              </div>
              <Progress
                percent={actionPlan.progress_percentage}
                strokeColor={{
                  "0%": "#108ee9",
                  "100%": "#87d068",
                }}
                className="mb-2"
              />
              <Text className="text-sm text-gray-500">
                {completedSteps} of {totalSteps} steps completed
              </Text>
            </div>
          </div>
        </div>
      </Card>

      {/* Tasks List */}
      <Card
        title={
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ListTodo className="h-5 w-5" />
              <span>Tasks</span>
            </div>
            <Button
              type="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setShowAddStepModal(true)}
            >
              Add Step
            </Button>
          </div>
        }
      >
        {actionPlan.steps.length > 0 ? (
          <div className="space-y-4">
            {actionPlan.steps.map((step) => (
              <Card
                key={step.id}
                className={`transition-all duration-200 ${
                  step.completed ? "bg-green-50 border-green-200" : "bg-white"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={step.completed}
                    onChange={(e) =>
                      handleStepStatusChange(step.id, e.target.checked)
                    }
                    className="mt-1"
                  />

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Text
                          strong
                          className={
                            step.completed ? "line-through text-gray-500" : ""
                          }
                        >
                          {step.title}
                        </Text>
                        {step.subtasks.length > 0 && (
                          <Tag color="blue">
                            {step.subtasks.length} subtasks
                          </Tag>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {step.due_date && (
                          <Text className="text-xs text-gray-500">
                            Due {new Date(step.due_date).toLocaleDateString()}
                          </Text>
                        )}
                        <Button
                          type="text"
                          size="small"
                          icon={<Plus className="h-3 w-3" />}
                          onClick={() => {
                            setSelectedStepId(step.id);
                            setShowAddSubtaskModal(true);
                          }}
                        >
                          Add Subtask
                        </Button>
                        {step.subtasks.length > 0 && (
                          <Button
                            type="text"
                            size="small"
                            icon={
                              expandedSteps.has(step.id) ? (
                                <ChevronDown className="h-3 w-3" />
                              ) : (
                                <ChevronRight className="h-3 w-3" />
                              )
                            }
                            onClick={() => toggleStepExpansion(step.id)}
                          />
                        )}
                      </div>
                    </div>

                    {step.description && (
                      <Paragraph
                        className={`text-sm text-gray-600 mb-3 ${
                          step.completed ? "line-through" : ""
                        }`}
                      >
                        {step.description}
                      </Paragraph>
                    )}

                    {step.notes && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-3">
                        <div className="flex items-center gap-1 mb-1">
                          <NotebookPen className="h-3 w-3 text-yellow-600" />
                          <Text className="text-xs font-medium text-yellow-800">
                            Notes
                          </Text>
                        </div>
                        <Text className="text-xs text-yellow-700">
                          {step.notes}
                        </Text>
                      </div>
                    )}

                    {/* Subtasks */}
                    {step.subtasks.length > 0 && expandedSteps.has(step.id) && (
                      <div className="ml-4 pl-4 border-l-2 border-gray-200 space-y-2">
                        {step.subtasks.map((subtask) => (
                          <div
                            key={subtask.id}
                            className="flex items-start gap-2"
                          >
                            <Checkbox
                              checked={subtask.completed}
                              onChange={(e) =>
                                handleSubtaskStatusChange(
                                  step.id,
                                  subtask.id,
                                  e.target.checked
                                )
                              }
                              className="mt-0.5"
                            />
                            <div className="flex-1">
                              <Text
                                className={`text-sm ${
                                  subtask.completed
                                    ? "line-through text-gray-500"
                                    : ""
                                }`}
                              >
                                {subtask.title}
                              </Text>
                              {subtask.description && (
                                <div className="text-xs text-gray-500 mt-1">
                                  {subtask.description}
                                </div>
                              )}
                              {subtask.due_date && (
                                <div className="text-xs text-gray-400 mt-1">
                                  Due{" "}
                                  {new Date(
                                    subtask.due_date
                                  ).toLocaleDateString()}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Empty description="No tasks yet">
            <Button
              type="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setShowAddStepModal(true)}
            >
              Add Your First Step
            </Button>
          </Empty>
        )}
      </Card>

      {/* Add Step Modal */}
      <Modal
        title="Add New Step"
        open={showAddStepModal}
        onCancel={() => {
          setShowAddStepModal(false);
          stepForm.resetFields();
        }}
        footer={null}
      >
        <Form form={stepForm} layout="vertical" onFinish={handleAddStep}>
          <Form.Item
            name="title"
            label="Step Title"
            rules={[{ required: true, message: "Please enter a title" }]}
          >
            <Input placeholder="e.g., Complete morning meditation" />
          </Form.Item>

          <Form.Item name="description" label="Description (Optional)">
            <TextArea
              rows={3}
              placeholder="Describe what this step involves..."
            />
          </Form.Item>

          <Form.Item name="due_date" label="Due Date (Optional)">
            <DatePicker className="w-full" />
          </Form.Item>

          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => {
                setShowAddStepModal(false);
                stepForm.resetFields();
              }}
            >
              Cancel
            </Button>
            <Button type="primary" htmlType="submit">
              Add Step
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Add Subtask Modal */}
      <Modal
        title="Add New Subtask"
        open={showAddSubtaskModal}
        onCancel={() => {
          setShowAddSubtaskModal(false);
          setSelectedStepId(null);
          subtaskForm.resetFields();
        }}
        footer={null}
      >
        <Form form={subtaskForm} layout="vertical" onFinish={handleAddSubtask}>
          <Form.Item
            name="title"
            label="Subtask Title"
            rules={[{ required: true, message: "Please enter a title" }]}
          >
            <Input placeholder="e.g., Set up meditation space" />
          </Form.Item>

          <Form.Item name="description" label="Description (Optional)">
            <TextArea
              rows={2}
              placeholder="Brief description of this subtask..."
            />
          </Form.Item>

          <Form.Item name="due_date" label="Due Date (Optional)">
            <DatePicker className="w-full" />
          </Form.Item>

          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => {
                setShowAddSubtaskModal(false);
                setSelectedStepId(null);
                subtaskForm.resetFields();
              }}
            >
              Cancel
            </Button>
            <Button type="primary" htmlType="submit">
              Add Subtask
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
