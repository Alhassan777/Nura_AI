import React, { useState } from "react";
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

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [isOpen, setIsOpen] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [, setUser] = useLocalStorage<User | null>("user", null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      // Set authentication cookie
      setCookie("token", "123");

      // In a real app, this would authenticate against a backend
      // For now, we'll simulate by checking if user exists in localStorage
      const existingUsers = JSON.parse(localStorage.getItem("users") || "[]");
      const existingUser = existingUsers.find(
        (user: any) => user.email === data.email
      );

      if (!existingUser) {
        toast.error("User not found. Please sign up first.");
        return;
      }

      // Set user data with voice integration compatibility
      const userData = {
        id: existingUser.id,
        email: existingUser.email,
        fullName: existingUser.fullName,
        phoneNumber: existingUser.phoneNumber,
        sub: existingUser.id, // Add sub field for voice compatibility
      };

      setUser(userData);
      toast.success("Login successful");
      setIsOpen(false);

      // Force a page refresh to update authentication state
      window.location.reload();
    } catch (error) {
      toast.error("Login failed");
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Login</Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Login</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  {...register("password")}
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
              {errors.password && (
                <p className="text-sm text-red-500">
                  {errors.password.message}
                </p>
              )}
            </div>

            <Button variant={"outline"} type="submit" className="w-full">
              Login
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
