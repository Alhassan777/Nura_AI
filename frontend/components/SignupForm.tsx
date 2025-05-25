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

const signupSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  fullName: z.string().min(3, "Full name must be at least 3 characters"),
  phoneNumber: z
    .string()
    .regex(
      /^\(\d{3}\) \d{3}-\d{4}$/,
      "Phone number must be in format (XXX) XXX-XXXX"
    ),
});

type SignupFormData = z.infer<typeof signupSchema>;

export type User = {
  id: string;
  email: string;
  fullName: string;
  phoneNumber: string;
};

export function SignupForm() {
  const [isOpen, setIsOpen] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [, setUser] = useLocalStorage<User | null>("user", null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: SignupFormData) => {
    try {
      setCookie("token", "123");
      setUser({
        id: "1",
        email: data.email,
        fullName: "John Doe",
        phoneNumber: "1234567890",
      });
      toast.success("Signup successful");
      setIsOpen(false);
    } catch (error) {
      console.log(error);
      toast.error("Signup failed");
    }
  };

  return (
    <>
      <Button variant={"outline"} onClick={() => setIsOpen(true)}>
        Sign Up
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Sign Up</DialogTitle>
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
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Enter your full name"
                {...register("fullName")}
              />
              {errors.fullName && (
                <p className="text-sm text-red-500">
                  {errors.fullName.message}
                </p>
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

            <div className="space-y-2">
              <Label htmlFor="phoneNumber">Phone Number</Label>
              <div className="flex">
                <div className="flex items-center justify-center px-3 bg-muted border border-r-0 rounded-l-md">
                  +1
                </div>
                <Input
                  id="phoneNumber"
                  type="tel"
                  placeholder="(XXX) XXX-XXXX"
                  className="rounded-l-none"
                  pattern="\(\d{3}\) \d{3}-\d{4}"
                  maxLength={14}
                  {...register("phoneNumber", {
                    onChange: (e) => {
                      const value = e.target.value.replace(/\D/g, "");
                      if (value.length <= 10) {
                        const formatted = value.replace(
                          /(\d{3})(\d{3})(\d{4})/,
                          "($1) $2-$3"
                        );
                        e.target.value = formatted;
                      }
                    },
                  })}
                />
              </div>
              {errors.phoneNumber && (
                <p className="text-sm text-red-500">
                  {errors.phoneNumber.message}
                </p>
              )}
            </div>

            <Button variant={"outline"} type="submit" className="w-full">
              Sign Up
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
