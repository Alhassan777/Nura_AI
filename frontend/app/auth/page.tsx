"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { useUser } from "../providers";
import { LoginForm } from "@/components/LoginForm";
import { SignupForm } from "@/components/SignupForm";

export default function AuthPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useUser();

  // Redirect to dashboard if already authenticated
  React.useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="absolute inset-0 pointer-events-none overflow-hidden -z-10"
      >
        <div className="absolute -inset-[10px] opacity-10">
          {/* Neo grid background */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px]"></div>

          {/* Gradient orbs */}
          <div className="absolute top-0 left-0 -mt-40 -ml-40 w-96 h-96 bg-primary/20 dark:bg-primary/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 -mb-40 -mr-40 w-96 h-96 bg-slate-400/20 dark:bg-slate-900/20 rounded-full blur-3xl"></div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-full max-w-md"
      >
        <Card className="backdrop-blur-sm bg-background/80 dark:bg-card/80 border-neutral-200/20 dark:border-neutral-800/50 overflow-hidden">
          <CardHeader className="pb-4 bg-gradient-to-r from-background/60 to-background/60 via-primary/5 dark:from-card/60 dark:to-card/60 dark:via-primary/10">
            <CardTitle className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
              Welcome to Nura
            </CardTitle>
            <CardDescription>
              Your mental health assistant powered by AI
            </CardDescription>
          </CardHeader>
          <CardContent className="py-6">
            <div className="space-y-6">
              <p className="text-center text-muted-foreground">
                Sign in or create an account to get started with your mental
                health journey
              </p>

              <div className="flex flex-col space-y-4">
                <div className="flex justify-center">
                  <LoginForm />
                </div>

                <div className="flex items-center my-4">
                  <div className="flex-1 border-t border-neutral-200/30 dark:border-neutral-800/50"></div>
                  <span className="mx-4 text-sm text-muted-foreground">or</span>
                  <div className="flex-1 border-t border-neutral-200/30 dark:border-neutral-800/50"></div>
                </div>

                <div className="flex justify-center">
                  <SignupForm />
                </div>
              </div>

              <div className="text-xs text-center text-muted-foreground mt-6">
                <p className="mb-1">
                  Your data is stored securely and privately.
                </p>
                <p>
                  Start your journey to better mental health with Nura's AI
                  assistant.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
