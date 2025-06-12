"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Result, Button } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";

export default function VerifyConfirmedPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to home page after 5 seconds
    const timer = setTimeout(() => {
      router.push("/");
    }, 5000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="h-full flex items-center justify-center">
      <div className="w-full max-w-md p-6">
        <Result
          status="success"
          icon={<CheckCircleOutlined className="text-green-500 text-6xl" />}
          title="Email Verified Successfully!"
          subTitle={
            <div className="space-y-4">
              <p className="text-gray-600">
                Your email has been verified. You can now access all features of
                your account.
              </p>
              <p className="text-sm text-gray-500">
                You will be redirected to the home page in a few seconds...
              </p>
            </div>
          }
          extra={[
            <Button
              key="home"
              type="primary"
              onClick={() => router.push("/")}
              size="large"
            >
              Go to Home Page
            </Button>,
          ]}
        />
      </div>
    </div>
  );
}
