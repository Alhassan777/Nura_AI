import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff } from "lucide-react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { setCookie } from "cookies-next";
import { useLocalStorage } from "usehooks-ts";
import { User } from "./SignupForm";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

const signupSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  username: z.string().min(3, "Username must be at least 3 characters"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;
type SignupFormData = z.infer<typeof signupSchema>;

interface AuthDialogProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: "login" | "signup";
  activeTab?: "login" | "signup";
  onTabChange?: (tab: "login" | "signup") => void;
}

export function AuthDialog({
  isOpen,
  onClose,
  defaultTab = "login",
  activeTab,
  onTabChange,
}: AuthDialogProps) {
  const [internalTab, setInternalTab] = useState<"login" | "signup">(
    defaultTab
  );
  const [showPassword, setShowPassword] = useState(false);
  const [, setUser] = useLocalStorage<User | null>("user", null);

  // Update internal tab when activeTab prop changes
  useEffect(() => {
    if (activeTab) {
      setInternalTab(activeTab);
    }
  }, [activeTab]);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const signupForm = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    mode: "onBlur",
  });

  const handleTabChange = (tab: "login" | "signup") => {
    setInternalTab(tab);
    onTabChange?.(tab);
  };

  const onLoginSubmit = async (data: LoginFormData) => {
    try {
      setCookie("token", "123");
      setUser({
        id: "1",
        email: data.email,
        fullName: "John Doe",
        phoneNumber: "1234567890",
      });
      toast.success("Login successful");
      onClose();
    } catch (error) {
      toast.error("Login failed");
    }
  };

  const onSignupSubmit = async (data: SignupFormData) => {
    try {
      setCookie("token", "123");
      setUser({
        id: "1",
        email: data.email,
        fullName: "John Doe",
        phoneNumber: "1234567890",
      });
      toast.success("Signup successful");
      onClose();
    } catch (error) {
      toast.error("Signup failed");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-center">Welcome to NeuraInk</DialogTitle>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex border-b border-gray-800 mb-6">
          <button
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              internalTab === "login"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-gray-300"
            }`}
            onClick={() => handleTabChange("login")}
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              internalTab === "signup"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-gray-300"
            }`}
            onClick={() => handleTabChange("signup")}
          >
            Sign Up
          </button>
        </div>

        {/* Login Form */}
        {internalTab === "login" && (
          <form
            onSubmit={loginForm.handleSubmit(onLoginSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                placeholder="Enter your email"
                {...loginForm.register("email")}
              />
              {loginForm.formState.errors.email && (
                <p className="text-sm text-red-500">
                  {loginForm.formState.errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="login-password">Password</Label>
              <div className="relative">
                <Input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  {...loginForm.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </button>
              </div>
              {loginForm.formState.errors.password && (
                <p className="text-sm text-red-500">
                  {loginForm.formState.errors.password.message}
                </p>
              )}
            </div>

            <Button type="submit" className="w-full">
              Login
            </Button>
          </form>
        )}

        {/* Signup Form */}
        {internalTab === "signup" && (
          <form
            onSubmit={signupForm.handleSubmit(onSignupSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                type="email"
                placeholder="Enter your email"
                {...signupForm.register("email")}
              />
              {signupForm.formState.errors.email && (
                <p className="text-sm text-red-500">
                  {signupForm.formState.errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-username">Username</Label>
              <Input
                id="signup-username"
                type="text"
                placeholder="Enter your username"
                {...signupForm.register("username")}
              />
              {signupForm.formState.errors.username && (
                <p className="text-sm text-red-500">
                  {signupForm.formState.errors.username.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password">Password</Label>
              <div className="relative">
                <Input
                  id="signup-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  {...signupForm.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-500" />
                  )}
                </button>
              </div>
              {signupForm.formState.errors.password && (
                <p className="text-sm text-red-500">
                  {signupForm.formState.errors.password.message}
                </p>
              )}
            </div>

            <Button type="submit" className="w-full">
              Sign Up
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
