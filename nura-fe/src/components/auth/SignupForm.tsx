"use client";

import { Button, Form, Input, Divider, App } from "antd";
import {
  GoogleOutlined,
  MailOutlined,
  LockOutlined,
  UserOutlined,
  PhoneOutlined,
} from "@ant-design/icons";
import { useState } from "react";
import Link from "next/link";
import { SignupFormData, USER } from "./types";
import { signup } from "@/utils/login-actions";
import { useLocalStorage } from "usehooks-ts";
import { useRouter } from "next/navigation";

export default function SignupForm() {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useLocalStorage<USER | null>("user", null);
  const router = useRouter();
  const { message } = App.useApp();

  const onFinish = async (values: SignupFormData) => {
    setLoading(true);
    try {
      console.log("Signup values:", values);
      const result = await signup(values);

      message.success(result.message || "Signup successful");

      setUser({
        fullName: values.fullName,
        email: values.email,
        phoneNumber: values.phoneNumber,
        isVerified: !result.email_verification_sent, // If email verification was sent, user is not verified yet
      });

      if (result.email_verification_sent) {
        router.push("/verify-email");
      } else {
        // User is already verified, redirect to main app
        router.push("/");
      }
    } catch (error) {
      console.error("Signup error:", error);
      message.error(error instanceof Error ? error.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setLoading(true);
    try {
      // TODO: Implement Google SSO logic here
      console.log("Google signup clicked");
      message.info("Google signup will be implemented soon");
    } catch (error) {
      console.error("Google signup error:", error);
    } finally {
      setLoading(false);
    }
  };

  // Phone number validation function
  const validatePhoneNumber = (_: any, value: string) => {
    if (!value) {
      return Promise.reject("Please input your phone number!");
    }

    // Remove any non-digit characters for validation
    const digitsOnly = value.replace(/\D/g, "");

    // Check if the number has the correct length (10 digits for US numbers)
    if (digitsOnly.length !== 10) {
      return Promise.reject("Please enter a valid 10-digit phone number!");
    }

    return Promise.resolve();
  };

  return (
    <div className="h-auto flex items-center justify-center w-full">
      <div className="w-full sm:max-w-md mx-auto sm:p-6 bg-white rounded-lg sm:shadow-sm sm:border sm:border-gray-200 h-fit flex flex-col items-center justify-center">
        <h1 className="text-2xl font-bold text-center mb-6">Create Account</h1>

        <Button
          type="default"
          icon={<GoogleOutlined />}
          size="large"
          block
          onClick={handleGoogleSignup}
          className="mb-4"
        >
          Sign up with Google
        </Button>

        <Divider className="my-4">or</Divider>

        <Form
          name="signup"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
          className="flex flex-col w-full"
        >
          <Form.Item
            name="fullName"
            rules={[
              { required: true, message: "Please input your full name!" },
              { min: 2, message: "Name must be at least 2 characters!" },
              {
                max: 100,
                message: "Name cannot be longer than 100 characters!",
              },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Full Name"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: "Please input your email!" },
              { type: "email", message: "Please enter a valid email!" },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
          </Form.Item>

          <Form.Item
            name="phoneNumber"
            rules={[
              { required: true, message: "Please input your phone number!" },
              { validator: validatePhoneNumber },
            ]}
          >
            <Input
              prefix={
                <div className="flex items-center">
                  <span className="text-gray-500 mr-1">+1</span>
                  <PhoneOutlined className="text-gray-400" />
                </div>
              }
              placeholder="(555) 555-5555"
              size="large"
              maxLength={14}
              onChange={(e) => {
                // Format phone number as user types
                const value = e.target.value.replace(/\D/g, "");
                if (value.length <= 10) {
                  const formatted = value.replace(
                    /(\d{3})(\d{3})(\d{4})/,
                    "($1) $2-$3"
                  );
                  e.target.value = formatted;
                }
              }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: "Please input your password!" },
              { min: 8, message: "Password must be at least 8 characters!" },
              {
                pattern:
                  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
                message:
                  "Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character!",
              },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={["password"]}
            rules={[
              { required: true, message: "Please confirm your password!" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Passwords do not match!"));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm Password"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
            >
              Create Account
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-purple-500">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
