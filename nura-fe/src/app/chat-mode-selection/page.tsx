"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Typography } from "antd";
import {
  MessageCircle,
  ArrowLeft,
  Heart,
  Target,
  Palette,
  Lightbulb,
  CheckCircle,
  Sparkles,
  Brain,
  Phone,
} from "lucide-react";
import { useRouter } from "next/navigation";

const { Title, Paragraph } = Typography;

export default function ChatModeSelectionPage() {
  const router = useRouter();

  const handleModeSelection = (mode: string) => {
    // Navigate to text-chat with the selected mode as a query parameter
    router.push(`/text-chat?mode=${mode}`);
  };

  return (
    <div className="container mx-auto p-4 h-screen flex flex-col">
      {/* Header */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                type="text"
                icon={<ArrowLeft className="h-4 w-4" />}
                onClick={() => router.back()}
              >
                Back
              </Button>
              <MessageCircle className="h-6 w-6 text-blue-600" />
              <div>
                <CardTitle className="!mb-1">Choose Your Chat Mode</CardTitle>
                <Paragraph className="text-sm text-gray-600 !mb-0">
                  Select the type of support that best fits your needs today
                </Paragraph>
              </div>
            </div>
            <Button
              type="default"
              icon={<Phone className="h-4 w-4" />}
              onClick={() => router.push("/voice-chat")}
            >
              Switch to Voice
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Mode Selection Cards */}
      <div className="flex-1 grid md:grid-cols-3 gap-6">
        {/* General Support Mode */}
        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center space-y-4 h-full flex flex-col">
            <div className="p-4 bg-blue-100 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
              <Heart className="h-8 w-8 text-blue-600" />
            </div>

            <div className="flex-1">
              <Title level={3} className="!mb-2 text-blue-700">
                General Support
              </Title>
              <Paragraph className="text-gray-600 text-sm mb-4">
                Emotional support and validation through active listening and
                empathetic responses.
              </Paragraph>

              <div className="space-y-2 text-left">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-blue-500" />
                  <span>Active listening and validation</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-blue-500" />
                  <span>Emotional processing support</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-blue-500" />
                  <span>Coping strategies and resources</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-blue-500" />
                  <span>Crisis intervention when needed</span>
                </div>
              </div>
            </div>

            <Button
              type="default"
              size="large"
              icon={<Heart className="h-4 w-4" />}
              onClick={() => handleModeSelection("general")}
              className="w-full"
            >
              Get Emotional Support
            </Button>
          </CardContent>
        </Card>

        {/* Action Plan Mode */}
        <Card className="hover:shadow-lg transition-shadow cursor-pointer border-2 border-purple-200">
          <CardContent className="p-6 text-center space-y-4 h-full flex flex-col">
            <div className="p-4 bg-purple-100 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
              <Target className="h-8 w-8 text-purple-600" />
            </div>

            <div className="flex-1">
              <Title level={3} className="!mb-2 text-purple-700">
                Action Planning
              </Title>
              <Paragraph className="text-gray-600 text-sm mb-4">
                Solution-oriented collaborative planning to help you achieve
                your goals step by step.
              </Paragraph>

              <div className="space-y-2 text-left">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-purple-500" />
                  <span>Goal setting and planning</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-purple-500" />
                  <span>Step-by-step action plans</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-purple-500" />
                  <span>Progress tracking support</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-purple-500" />
                  <span>Practical problem-solving</span>
                </div>
              </div>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<Target className="h-4 w-4" />}
              onClick={() => handleModeSelection("action_plan")}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              Create Action Plan
            </Button>
          </CardContent>
        </Card>

        {/* Visualization Mode */}
        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center space-y-4 h-full flex flex-col">
            <div className="p-4 bg-green-100 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
              <Palette className="h-8 w-8 text-green-600" />
            </div>

            <div className="flex-1">
              <Title level={3} className="!mb-2 text-green-700">
                Creative Expression
              </Title>
              <Paragraph className="text-gray-600 text-sm mb-4">
                Express your emotions through visual art and creative metaphors
                for deeper understanding.
              </Paragraph>

              <div className="space-y-2 text-left">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Emotional art generation</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Visual metaphor exploration</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Creative therapy techniques</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Non-verbal expression support</span>
                </div>
              </div>
            </div>

            <Button
              type="default"
              size="large"
              icon={<Palette className="h-4 w-4" />}
              onClick={() => handleModeSelection("visualization")}
              className="w-full border-green-500 text-green-600 hover:bg-green-50"
            >
              Start Drawing
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Info Section */}
      <Card className="mt-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-blue-500" />
              <span>All modes include memory management</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span>AI auto-detects the best mode for your needs</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
