"use client";

import { useState } from "react";
import { Modal, Form, Input, Select, Button, message } from "antd";
import { UserAddOutlined } from "@ant-design/icons";
import {
  useSearchUsers,
  useSendInvitation,
} from "@/services/hooks/use-safety-invitations";

const { Option } = Select;

interface AddContactModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormData {
  email: string;
  relationship_type: string;
  message: string;
}

export const AddContactModal = ({ isOpen, onClose }: AddContactModalProps) => {
  const [form] = Form.useForm();
  const [isLoading, setIsLoading] = useState(false);

  const searchUsersMutation = useSearchUsers();
  const sendInvitationMutation = useSendInvitation();

  const handleSubmit = async (values: FormData) => {
    try {
      setIsLoading(true);

      await sendInvitationMutation.mutateAsync({
        recipient_email: values.email,
        relationship_type: values.relationship_type,
        requested_permissions: {
          can_view_mood: true,
          can_receive_alerts: true,
        },
        invitation_message: values.message,
      });

      message.success("Invitation sent successfully!");
      form.resetFields();
      onClose();
    } catch (error: any) {
      console.error("Error sending invitation:", error);

      // Extract error message from response
      let errorMessage = "Failed to send invitation";
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.message) {
        errorMessage = error.message;
      }

      message.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center space-x-2">
          <UserAddOutlined />
          <span>Add to Safety Network</span>
        </div>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        className="mt-4"
      >
        <Form.Item
          name="email"
          label="Email Address"
          rules={[
            { required: true, message: "Please enter an email address" },
            { type: "email", message: "Please enter a valid email address" },
          ]}
        >
          <Input placeholder="Enter contact's email address" size="large" />
        </Form.Item>

        <Form.Item
          name="relationship_type"
          label="Relationship"
          rules={[
            { required: true, message: "Please select a relationship type" },
          ]}
        >
          <Select placeholder="Select relationship type" size="large">
            <Option value="family">Family Member</Option>
            <Option value="friend">Friend</Option>
            <Option value="partner">Partner/Spouse</Option>
            <Option value="therapist">Therapist/Counselor</Option>
            <Option value="healthcare">Healthcare Provider</Option>
            <Option value="colleague">Colleague</Option>
            <Option value="mentor">Mentor</Option>
            <Option value="other">Other</Option>
          </Select>
        </Form.Item>

        <Form.Item name="message" label="Personal Message (Optional)">
          <Input.TextArea
            placeholder="Add a personal message to your invitation..."
            rows={3}
            maxLength={500}
            showCount
          />
        </Form.Item>

        <Form.Item className="mb-0">
          <div className="flex justify-end space-x-2">
            <Button onClick={onClose}>Cancel</Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              icon={<UserAddOutlined />}
            >
              Send Invitation
            </Button>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
};
