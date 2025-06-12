"use client";

import { Modal, Form, Input, Button, Upload, Avatar, App } from "antd";
import { UserOutlined, CameraOutlined } from "@ant-design/icons";
import { useState, useEffect } from "react";
import { userApi } from "@/services/apis";
import { useAuth } from "@/contexts/AuthContext";

interface EditProfileModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface ProfileFormData {
  full_name: string;
  display_name: string;
  bio: string;
  avatar_url?: string;
}

const EditProfileModal: React.FC<EditProfileModalProps> = ({
  visible,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const { user, refreshUser } = useAuth();
  const { message } = App.useApp();

  // Initialize form with current user data
  useEffect(() => {
    if (visible && user) {
      form.setFieldsValue({
        full_name: user.full_name || "",
        display_name: user.display_name || "",
        bio: user.bio || "",
      });
      // Only set avatarUrl if it exists and is not empty
      setAvatarUrl(
        user.avatar_url && user.avatar_url.trim() ? user.avatar_url : null
      );
    }
  }, [visible, user, form]);

  const handleSubmit = async (values: ProfileFormData) => {
    setLoading(true);
    try {
      const updateData = {
        full_name: values.full_name || null,
        display_name: values.display_name || null,
        bio: values.bio || null,
        avatar_url: avatarUrl || null,
      };

      await userApi.updateProfile(updateData);

      message.success("Profile updated successfully!");

      // Refresh user data in context
      await refreshUser();

      // Call success callback and close modal
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error("Profile update error:", error);
      message.error(
        error.response?.data?.message ||
          error.message ||
          "Failed to update profile. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setAvatarUrl(
      user?.avatar_url && user.avatar_url.trim() ? user.avatar_url : null
    );
    onClose();
  };

  // Handle avatar upload (placeholder for now)
  const handleAvatarChange = (info: any) => {
    // This is a placeholder for avatar upload functionality
    // In a real implementation, you would:
    // 1. Upload the file to a cloud storage service (AWS S3, Cloudinary, etc.)
    // 2. Get back a URL to store in avatar_url
    // 3. Update the avatarUrl state with the new URL

    message.info({
      content:
        "Avatar upload functionality coming soon! You can update other profile information for now.",
      duration: 3,
    });
  };

  return (
    <Modal
      title="Edit Profile"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={500}
      destroyOnHidden
    >
      <div className="py-4">
        {/* Avatar Section */}
        <div className="flex flex-col items-center mb-6">
          <div className="relative">
            <Avatar
              size={80}
              src={avatarUrl || undefined}
              icon={!avatarUrl && <UserOutlined />}
              className="mb-3"
            />
            <Upload
              showUploadList={false}
              beforeUpload={() => false} // Prevent auto upload
              onChange={handleAvatarChange}
              accept="image/*"
            >
              <Button
                type="text"
                icon={<CameraOutlined />}
                className="absolute -bottom-1 -right-1 bg-white rounded-full border border-gray-300 hover:bg-gray-50 shadow-sm"
                size="small"
                title="Upload avatar (coming soon)"
              />
            </Upload>
          </div>
          <p className="text-sm text-gray-500 text-center">
            Click camera to change avatar
            <br />
            <span className="text-xs text-gray-400">
              (Upload feature coming soon)
            </span>
          </p>
        </div>

        {/* Profile Form */}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className="space-y-4"
        >
          <Form.Item
            label="Full Name"
            name="full_name"
            rules={[
              { required: true, message: "Please enter your full name" },
              { min: 2, message: "Full name must be at least 2 characters" },
              {
                max: 100,
                message: "Full name must be less than 100 characters",
              },
            ]}
          >
            <Input placeholder="Enter your full name" size="large" />
          </Form.Item>

          <Form.Item
            label="Display Name"
            name="display_name"
            rules={[
              { min: 2, message: "Display name must be at least 2 characters" },
              {
                max: 50,
                message: "Display name must be less than 50 characters",
              },
            ]}
          >
            <Input placeholder="How others will see your name" size="large" />
          </Form.Item>

          <Form.Item
            label="Bio"
            name="bio"
            rules={[
              { max: 500, message: "Bio must be less than 500 characters" },
            ]}
          >
            <Input.TextArea
              placeholder="Tell us about yourself..."
              rows={4}
              showCount
              maxLength={500}
            />
          </Form.Item>

          {/* Form Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="default"
              onClick={handleCancel}
              className="flex-1"
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 border-blue-600"
            >
              Save Changes
            </Button>
          </div>
        </Form>
      </div>
    </Modal>
  );
};

export default EditProfileModal;
