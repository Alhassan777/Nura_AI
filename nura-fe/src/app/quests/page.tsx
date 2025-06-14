"use client";

import React, { useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Star, BookOpen, Plus, Check } from "lucide-react";
import {
  useCreateQuest,
  useQuests,
  useCompleteQuest,
} from "@/services/hooks/use-quests";
import { CreateQuestType, Quest } from "../api/gamification/quests/utils";
import { Button, Form, Input, Select, InputNumber, Modal, message } from "antd";
import { cn } from "@/lib/utils";

const { TextArea } = Input;
const { Option } = Select;

const QuestCard = ({ quest }: { quest: Quest }) => {
  const { mutateAsync: completeQuest, isPending: isCompleting } =
    useCompleteQuest();

  const progressPercent =
    ((quest?.progress?.count ?? 0) / quest?.frequency) * 100;
  const isCompleted =
    quest.type === "system"
      ? (quest?.progress?.count ?? 0) >= quest?.frequency
      : quest?.progress?.status === "COMPLETED";

  const handleCompleteQuest = async () => {
    try {
      const result = await completeQuest(quest.id);
      if (result.completed) {
        message.success("Quest completed successfully! XP awarded!");
      } else {
        message.success(
          `Progress updated! ${result.progress}/${result.total} completed`
        );
      }
    } catch (error: any) {
      message.error(error.response?.data?.error || "Failed to complete quest");
    }
  };

  return (
    <Card
      className={`bg-white backdrop-blur-3xl p-4 shadow-xs border-2 transition-all duration-200 ${
        isCompleted ? " border-green-500" : "hover:shadow-md border-purple-500"
      }`}
    >
      <div className="flex items-start gap-4 h-full">
        <div className="h-10 w-10 rounded-full flex items-center justify-center bg-gray-100 border border-gray-200">
          {quest.key === "reflections" ? (
            <BookOpen className={cn(isCompleted && "text-green-500")} />
          ) : (
            <Trophy className={cn(isCompleted && "text-green-500")} />
          )}
        </div>

        <div className="flex-1 h-full flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-medium text-gray-900">{quest.title}</h3>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={cn(
                    "bg-purple-50 text-purple-700 border-purple-200 font-semibold",
                    isCompleted && "!text-green-700 border-green-500"
                  )}
                >
                  {quest.xp_reward} XP
                </Badge>
                {quest.type === "user" && (
                  <Badge
                    variant="outline"
                    className={cn(
                      "bg-purple-50 text-purple-700 border-purple-200 font-semibold",
                      isCompleted && "!text-green-700 border-green-500"
                    )}
                  >
                    Custom
                  </Badge>
                )}
              </div>
            </div>

            <p className="text-sm text-gray-600 mb-2">
              {quest?.description ?? "No description"}
            </p>

            <div className="space-y-1">
              <Progress value={progressPercent} className={`h-2`} />
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>
                  {quest.progress.count || 0} of {quest.frequency} completed
                </span>
                <span>{progressPercent.toFixed(0)}%</span>
              </div>
            </div>
          </div>
          {quest.type === "user" && !isCompleted && (
            <div className="flex justify-end mt-2">
              <Button
                type="primary"
                size="small"
                icon={<Check className="h-3 w-3" />}
                onClick={handleCompleteQuest}
                loading={isCompleting}
              >
                {quest.frequency === 1 ? "Mark Complete" : "Add Progress"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

const CreateQuestModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const [form] = Form.useForm();
  const { mutateAsync: createQuest, isPending } = useCreateQuest();
  const handleSubmit = async (values: CreateQuestType) => {
    try {
      await createQuest(values);
      message.success("Quest created successfully!");
      form.resetFields();
      onClose();
    } catch (error) {
      message.error("Failed to create quest");
      console.error(error);
    }
  };

  return (
    <Modal
      title="Create Custom Quest"
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          time_frame: "daily",
          frequency: 1,
          xp_reward: 50,
        }}
      >
        <Form.Item
          name="title"
          label="Quest Title"
          rules={[{ required: true, message: "Please enter a quest title" }]}
        >
          <Input placeholder="e.g., Read 30 minutes daily" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: false, message: "Please enter a description" }]}
        >
          <TextArea
            rows={3}
            placeholder="Describe what needs to be accomplished..."
          />
        </Form.Item>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            name="time_frame"
            label="Time Frame"
            rules={[{ required: true, message: "Please select a time frame" }]}
          >
            <Select placeholder="Select time frame">
              <Option value="daily">Daily</Option>
              <Option value="weekly">Weekly</Option>
              <Option value="monthly">Monthly</Option>
              <Option value="one_time">One Time Only</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="frequency"
            label="Frequency"
            rules={[{ required: true, message: "Please enter frequency" }]}
          >
            <InputNumber
              min={1}
              max={100}
              placeholder="How many times?"
              className="w-full"
            />
          </Form.Item>
        </div>

        <Form.Item
          name="xp_reward"
          label="XP Reward"
          rules={[{ required: true, message: "Please enter XP reward" }]}
        >
          <InputNumber
            min={10}
            max={1000}
            step={10}
            placeholder="XP to award"
            className="w-full"
          />
        </Form.Item>

        <div className="flex justify-end gap-2 mt-6">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" htmlType="submit" loading={isPending}>
            Create Quest
          </Button>
        </div>
      </Form>
    </Modal>
  );
};

export default function QuestsPage() {
  const { data: quests, isLoading, isError } = useQuests();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading quests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Quests</h1>
          <p className="text-gray-600">
            Complete quests to earn XP and unlock rewards
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-semibold text-gray-800">Your Progress</h2>
              <p className="text-sm text-gray-600">
                Keep completing quests to level up
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                Level 3
              </div>
              <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                1250 XP
              </div>
            </div>
          </div>
          <Progress value={45} className="h-3 bg-gray-200" />
          <div className="flex justify-between mt-1 text-xs text-gray-500">
            <span>1250 XP</span>
            <span>2500 XP needed for Level 4</span>
          </div>
        </div>

        {/* System Quests Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              System Quests
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quests?.systemQuests?.map((quest) => (
              <QuestCard key={quest.id} quest={quest} />
            ))}
          </div>

          {(!quests?.systemQuests || quests.systemQuests.length === 0) && (
            <div className="text-center py-10 bg-gray-50 rounded-lg">
              <Trophy className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No system quests available.</p>
            </div>
          )}
        </div>

        {/* User Quests Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Your Quests</h2>
            <Button
              type="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setIsCreateModalOpen(true)}
              className="bg-purple-600 hover:bg-purple-700 border-purple-600"
            >
              Create Quest
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quests?.userQuests?.map((quest) => (
              <QuestCard key={quest.id} quest={quest} />
            ))}
          </div>

          {(!quests?.userQuests || quests.userQuests.length === 0) && (
            <div className="text-center py-10 bg-gray-50 rounded-lg">
              <div className="max-w-md mx-auto">
                <Star className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Custom Quests Yet
                </h3>
                <p className="text-gray-500 mb-4">
                  Create your own personalized quests to track your goals and
                  earn XP.
                </p>
                <Button
                  type="primary"
                  icon={<Plus className="h-4 w-4" />}
                  onClick={() => setIsCreateModalOpen(true)}
                  className="bg-purple-600 hover:bg-purple-700 border-purple-600"
                >
                  Create Your First Quest
                </Button>
              </div>
            </div>
          )}
        </div>

        <CreateQuestModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </div>
    </div>
  );
}
