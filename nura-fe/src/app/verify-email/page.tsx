"use client";

import { Button, Card, message, Typography } from "antd";
import { MailOutlined, ReloadOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useLocalStorage } from "usehooks-ts";
import { USER } from "@/components/auth/types";
import { resendVerification } from "@/utils/login-actions";

const { Title, Text } = Typography;

export default function VerifyEmailPage() {
  const [loading, setLoading] = useState(false);
  const [user] = useLocalStorage<USER | null>("user", null);

  const handleResendVerification = async () => {
    if (!user?.email) return;

    setLoading(true);
    try {
      await resendVerification(user.email);
      message.success("Verification email sent");
    } catch (error) {
      console.error("Error resending verification:", error);
      message.error("Error resending verification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center">
      <Card
        rootClassName="!border-0 sm:!border-1"
        className="w-full sm:max-w-md "
        classNames={{
          body: "sm:!p-4 !p-0",
        }}
      >
        <div className="text-center">
          <MailOutlined className="text-4xl text-blue-500 mb-4" />
          <Title level={2}>Verify your email</Title>

          <Text className="block text-gray-600 mb-6">
            We&apos;ve sent a verification link to{" "}
            <span className="font-semibold">{user?.email}</span>
          </Text>

          <div className="space-y-4">
            <Text className="block text-gray-600">
              Please check your email and click the verification link to
              continue.
            </Text>

            <div className="text-sm text-gray-500">
              <p>Didn&apos;t receive the email?</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Check your spam folder</li>
                <li>Make sure the email address is correct</li>
                <li>Wait a few minutes and try again</li>
              </ul>
            </div>

            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleResendVerification}
              loading={loading}
              block
            >
              Resend verification email
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
