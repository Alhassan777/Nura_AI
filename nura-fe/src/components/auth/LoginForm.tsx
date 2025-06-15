"use client";

import { Button, Form, Input, Divider, App } from "antd";
import { GoogleOutlined, MailOutlined, LockOutlined } from "@ant-design/icons";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "@/utils/login-actions";
import { useAuth } from "@/contexts/AuthContext";
import { useSetCookie } from "cookies-next/client";
import { createClient } from "@/utils/supabase/client";

export interface LoginFormData {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  phone_number?: string;
  is_verified: boolean;
}

export default function LoginForm() {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const router = useRouter();
  const { refreshUser, setUser } = useAuth();
  const { message } = App.useApp();
  const setCookie = useSetCookie();

  const supabase = createClient();

  const onFinish = async (values: LoginFormData) => {
    setLoading(true);

    try {
      console.log("Login values:", values);
      const result = await login(values);

      // Store tokens in localStorage
      if (typeof window !== "undefined" && result.token) {
        localStorage.setItem("auth_token", result.token);
        setCookie("auth_token", result.token);
        if (result.session.refresh_token) {
          localStorage.setItem("refresh_token", result.session.refresh_token);
        }
      }

      const { data, error } = await supabase.auth.setSession({
        access_token: result.token,
        refresh_token: result.session.refresh_token,
      });
      console.log("data", data);
      console.log("error", error);

      message.success("Login successful");

      // Set user in auth context immediately
      setUser(result.user);

      // Also refresh to ensure backend sync
      setTimeout(refreshUser, 100);

      // Redirect to dashboard
      router.push("/");
    } catch (error) {
      console.error("Login error:", error);
      // Show error message to user
      const errorMessage =
        error instanceof Error ? error.message : "Invalid email or password";
      message.error(errorMessage);
      form.setFields([
        {
          name: "email",
          errors: [errorMessage],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      // TODO: Implement Google SSO logic here
      console.log("Google login clicked");
      message.info("Google login will be implemented soon");
    } catch (error) {
      console.error("Google login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-auto flex items-center justify-center w-full">
      <div className="w-full sm:max-w-md mx-auto sm:p-6 bg-white rounded-lg sm:shadow-sm sm:border sm:border-gray-200 h-fit flex flex-col items-center justify-center">
        <h1 className="text-2xl font-bold text-center mb-6">Welcome Back</h1>

        <Button
          type="default"
          icon={<GoogleOutlined />}
          size="large"
          block
          onClick={handleGoogleLogin}
          className="mb-4"
        >
          Continue with Google
        </Button>

        <Divider className="my-4">or</Divider>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
          className="flex flex-col gap-4 w-full"
          validateTrigger={["onBlur", "onChange"]}
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: "Please input your email!" },
              { type: "email", message: "Please enter a valid email!" },
              {
                whitespace: true,
                message: "Email cannot be empty!",
              },
              {
                max: 100,
                message: "Email cannot be longer than 100 characters!",
              },
            ]}
            validateFirst
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
              autoComplete="email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: "Please input your password!" },
              {
                min: 8,
                message: "Password must be at least 8 characters!",
              },
              {
                max: 100,
                message: "Password cannot be longer than 100 characters!",
              },
            ]}
            validateFirst
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
              autoComplete="current-password"
              name="password"
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
              Sign In
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center space-y-2">
          <div>
            <Link
              href="/forgot-password"
              className="text-purple-500 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <div>
            Don't have an account?{" "}
            <Link href="/signup" className="text-purple-500">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
