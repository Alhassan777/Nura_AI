"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Typography } from "antd";
import { MessageCircle, Phone, Heart, Zap, Shield, Clock } from "lucide-react";
import { useRouter } from "next/navigation";

const { Title, Paragraph, Text } = Typography;

export default function ChatPage() {
  const router = useRouter();

  return (
    <div className="w-full">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Title level={1} className="!mb-0">
            Connect with Nura
          </Title>
          <Heart className="h-10 w-10 text-purple-600" />
        </div>
        <Paragraph className="text-lg !text-gray-400 max-w-2xl">
          Choose how you'd like to communicate with Nura today. Whether through
          thoughtful text conversations or intimate voice calls, Nura is here to
          support your mental wellness journey.
        </Paragraph>
      </div>

      {/* Communication Options */}
      <div className="grid md:grid-cols-2 gap-8  mx-auto">
        {/* Text Chat Option */}
        <Card>
          <CardContent className="p-8 text-center space-y-6">
            <div className="p-6 bg-blue-100 rounded-full w-24 h-24 mx-auto flex items-center justify-center">
              <MessageCircle className="h-12 w-12 text-blue-600" />
            </div>

            <div>
              <Title level={2} className="!mb-3">
                Text Chat
              </Title>
              <Paragraph className="text-gray-600 text-base">
                Engage in thoughtful, written conversations with Nura. Perfect
                for when you want to take your time expressing complex thoughts
                and feelings.
              </Paragraph>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Zap className="h-4 w-4 text-blue-500" />
                <span>Instant crisis support detection</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Shield className="h-4 w-4 text-blue-500" />
                <span>Private and secure messaging</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4 text-blue-500" />
                <span>Take your time to respond</span>
              </div>
            </div>

            <Button
              type="default"
              size="large"
              icon={<MessageCircle className="h-5 w-5" />}
              onClick={() => router.push("/text-chat")}
              className="w-full h-12 text-base"
            >
              Start Text Conversation
            </Button>
          </CardContent>
        </Card>

        {/* Voice Chat Option */}
        <Card>
          <CardContent className="p-8 text-center space-y-6">
            <div className="p-6 bg-purple-100 rounded-full w-24 h-24 mx-auto flex items-center justify-center">
              <Phone className="h-12 w-12 text-purple-600" />
            </div>

            <div>
              <Title level={2} className="!mb-3">
                Voice Chat
              </Title>
              <Paragraph className="text-gray-600 text-base">
                Experience a deeper emotional connection through voice
                conversations. Hear Nura's compassionate tone and express
                yourself naturally.
              </Paragraph>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Heart className="h-4 w-4 text-purple-500" />
                <span>Emotional tone recognition</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Zap className="h-4 w-4 text-purple-500" />
                <span>Real-time crisis intervention</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4 text-purple-500" />
                <span>Natural conversation flow</span>
              </div>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<Phone className="h-5 w-5" />}
              onClick={() => router.push("/voice-chat")}
              className="w-full h-12 text-base"
            >
              Start Voice Call
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-center">Need Immediate Support?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button
              type="default"
              size="large"
              className="h-12"
              onClick={() => router.push("/safety-network")}
            >
              Contact Safety Network
            </Button>
            <Button
              type="default"
              size="large"
              className="h-12"
              onClick={() => router.push("/crisis-resources")}
            >
              Crisis Resources
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
