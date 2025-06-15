"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Button,
  Typography,
  Space,
  Badge,
  Avatar,
  Modal,
  Input,
  message as antMessage,
} from "antd";
import {
  Phone,
  PhoneCall,
  MessageCircle,
  ArrowLeft,
  Clock,
  Mic,
  MicOff,
  PhoneOff,
  Heart,
  Volume2,
} from "lucide-react";
import { VoiceChat } from "@/components/voice/VoiceChat";
import { useRouter } from "next/navigation";
import { voiceApi } from "@/services/apis/voice";

const { Title, Paragraph, Text } = Typography;

type CallMode = "outgoing" | "incoming" | "active" | "idle";

export default function VoiceChatPage() {
  const router = useRouter();
  const [callMode, setCallMode] = useState<CallMode>("idle");
  const [showIncomingCall, setShowIncomingCall] = useState(false);
  const [showPhoneNumberModal, setShowPhoneNumberModal] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isInitiatingCall, setIsInitiatingCall] = useState(false);

  const handleCallNura = () => {
    setCallMode("outgoing");
    // Simulate connection delay
    setTimeout(() => {
      setCallMode("active");
    }, 2000);
  };

  const handleNuraCallsYou = () => {
    setShowPhoneNumberModal(true);
  };

  const handleInitiateOutboundCall = async () => {
    if (!phoneNumber.trim()) {
      antMessage.error("Please enter a valid phone number");
      return;
    }

    setIsInitiatingCall(true);

    try {
      // Format phone number (remove spaces, dashes, parentheses)
      const formattedPhone = phoneNumber.replace(/[\s\-\(\)\.]/g, "");

      // Validate phone number format (basic validation)
      const phoneRegex = /^\+?[1-9]\d{7,14}$/;
      if (!phoneRegex.test(formattedPhone)) {
        antMessage.error(
          "Please enter a valid phone number with country code (e.g., +1234567890)"
        );
        return;
      }

      // Ensure phone number starts with +
      const finalPhone = formattedPhone.startsWith("+")
        ? formattedPhone
        : `+${formattedPhone}`;

      // Get assistant ID with fallback
      const assistantId = process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID;
      if (!assistantId) {
        antMessage.error(
          "Assistant configuration is missing. Please contact support."
        );
        return;
      }

      // Make the outbound call
      const response = await voiceApi.createPhoneCall({
        assistant_id: assistantId,
        phone_number: finalPhone,
        metadata: {
          request_type: "user_requested_callback",
          timestamp: new Date().toISOString(),
        },
      });

      if (response.call_id) {
        antMessage.success(
          "Call initiated! Nura will call you shortly at " + finalPhone
        );
        setShowPhoneNumberModal(false);
        setPhoneNumber("");

        // Show confirmation that call is being initiated
        Modal.success({
          title: "Call Requested",
          content: `Nura is calling you at ${finalPhone}. Please answer when your phone rings!`,
          onOk: () => {
            router.push("/chat");
          },
        });
      }
    } catch (error: any) {
      console.error("Error initiating outbound call:", error);

      // Better error handling
      let errorMessage = "Failed to initiate call. Please try again.";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      antMessage.error(errorMessage);
    } finally {
      setIsInitiatingCall(false);
    }
  };

  const handleAnswerCall = () => {
    setShowIncomingCall(false);
    setCallMode("active");
  };

  const handleRejectCall = () => {
    setShowIncomingCall(false);
    setCallMode("idle");
  };

  const handleEndCall = () => {
    setCallMode("idle");
    // Redirect to chat page after call ends
    router.push("/chat");
  };

  const handleSwitchToText = () => {
    router.push("/text-chat");
  };

  if (callMode === "active") {
    return (
      <div className="container mx-auto p-4">
        <div className="mb-4">
          <Button
            type="text"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => router.back()}
          >
            Back to Chat Options
          </Button>
        </div>
        <VoiceChat
          onEndCall={handleEndCall}
          onSwitchToChat={handleSwitchToText}
          assistantId={process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID}
        />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <Card>
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
              <Phone className="h-6 w-6 text-purple-600" />
              <div>
                <CardTitle className="!mb-1">Voice Communication</CardTitle>
                <Paragraph className="text-sm text-gray-600 !mb-0">
                  Connect with Nura through voice conversation
                </Paragraph>
              </div>
            </div>
            <Button
              type="default"
              icon={<MessageCircle className="h-4 w-4" />}
              onClick={handleSwitchToText}
            >
              Switch to Text
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Call Options */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Call Nura Option */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6 text-center space-y-4">
            <div className="p-4 bg-green-100 rounded-full w-20 h-20 mx-auto flex items-center justify-center">
              <PhoneCall className="h-10 w-10 text-green-600" />
            </div>
            <div>
              <Title level={3} className="!mb-2">
                Call Nura
              </Title>
              <Paragraph className="text-gray-600">
                Initiate a voice call with Nura whenever you need support,
                guidance, or just someone to talk to.
              </Paragraph>
            </div>
            <Button
              type="primary"
              size="large"
              icon={<Phone className="h-5 w-5" />}
              onClick={handleCallNura}
              loading={callMode === "outgoing"}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {callMode === "outgoing" ? "Calling Nura..." : "Call Now"}
            </Button>
          </CardContent>
        </Card>

        {/* Nura Calls You Option */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6 text-center space-y-4">
            <div className="p-4 bg-purple-100 rounded-full w-20 h-20 mx-auto flex items-center justify-center">
              <Heart className="h-10 w-10 text-purple-600" />
            </div>
            <div>
              <Title level={3} className="!mb-2">
                Nura Calls You
              </Title>
              <Paragraph className="text-gray-600">
                Let Nura reach out to you for scheduled check-ins, wellness
                calls, or when she senses you might need support.
              </Paragraph>
            </div>
            <Button
              type="primary"
              size="large"
              icon={<Volume2 className="h-5 w-5" />}
              onClick={handleNuraCallsYou}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              Request Nura to Call
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Call Features */}
      <Card>
        <CardHeader>
          <CardTitle>Voice Chat Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center p-4">
              <Mic className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <Text strong>Natural Conversation</Text>
              <div className="text-sm text-gray-600 mt-1">
                Speak naturally and Nura will understand and respond with
                empathy
              </div>
            </div>
            <div className="text-center p-4">
              <Clock className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <Text strong>Crisis Support</Text>
              <div className="text-sm text-gray-600 mt-1">
                Immediate voice support during difficult moments with real-time
                crisis detection
              </div>
            </div>
            <div className="text-center p-4">
              <Heart className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <Text strong>Emotional Connection</Text>
              <div className="text-sm text-gray-600 mt-1">
                Experience a deeper emotional connection through voice and tone
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Incoming Call Modal */}
      <Modal
        open={showIncomingCall}
        closable={false}
        footer={null}
        width={400}
        centered
      >
        <div className="text-center space-y-6 py-4">
          <div className="relative">
            <Avatar
              size={120}
              className="bg-purple-600 mx-auto"
              icon={<Heart className="h-12 w-12" />}
            />
            <div className="absolute -top-2 -right-2">
              <Badge status="processing" />
            </div>
          </div>

          <div>
            <Title level={3} className="!mb-2">
              Nura is calling you
            </Title>
            <Text className="text-gray-600">
              Nura would like to check in on how you're feeling today
            </Text>
          </div>

          <div className="flex justify-center gap-4">
            <Button
              type="primary"
              size="large"
              shape="circle"
              icon={<Phone className="h-6 w-6" />}
              onClick={handleAnswerCall}
              className="w-16 h-16 bg-green-600 hover:bg-green-700 flex items-center justify-center"
            />
            <Button
              danger
              size="large"
              shape="circle"
              icon={<PhoneOff className="h-6 w-6" />}
              onClick={handleRejectCall}
              className="w-16 h-16 flex items-center justify-center"
            />
          </div>

          <div className="flex justify-center gap-8 text-sm text-gray-600">
            <span>Answer</span>
            <span>Decline</span>
          </div>
        </div>
      </Modal>

      {/* Phone Number Modal */}
      <Modal
        open={showPhoneNumberModal}
        closable={false}
        footer={null}
        width={400}
        centered
      >
        <div className="text-center space-y-6 py-4">
          <div>
            <Title level={3} className="!mb-2">
              Enter Your Phone Number
            </Title>
            <Text className="text-gray-600">
              We'll call you at the number you provide.
            </Text>
          </div>

          <Input
            type="tel"
            placeholder="e.g., +1 555-123-4567"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            className="w-full"
            size="large"
          />

          <Paragraph className="text-sm text-gray-500 !mb-0">
            Enter your phone number with country code (e.g., +1 for US)
          </Paragraph>

          <div className="flex gap-3">
            <Button
              size="large"
              onClick={() => {
                setShowPhoneNumberModal(false);
                setPhoneNumber("");
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="primary"
              size="large"
              icon={<Phone className="h-5 w-5" />}
              onClick={handleInitiateOutboundCall}
              loading={isInitiatingCall}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
              disabled={!phoneNumber.trim()}
            >
              {isInitiatingCall ? "Initiating Call..." : "Request Call"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
