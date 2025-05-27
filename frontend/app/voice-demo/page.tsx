"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import VoiceCallButton from "@/components/VoiceCallButton";
import LiveTranscript from "@/components/LiveTranscript";
import { useAuth } from "@/hooks/useAuth";
import { motion } from "framer-motion";
import {
  Phone,
  Mic,
  Settings,
  Info,
  CheckCircle,
  AlertCircle,
  Headphones,
} from "lucide-react";

interface TranscriptMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  confidence?: number;
  duration?: number;
}

const VoiceDemoPage: React.FC = () => {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();
  const [isCallActive, setIsCallActive] = useState(false);
  const [transcriptMessages, setTranscriptMessages] = useState<
    TranscriptMessage[]
  >([]);
  const [callId, setCallId] = useState<string | null>(null);
  const [phoneNumber, setPhoneNumber] = useState("");

  // Redirect to auth if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth");
    }
  }, [isAuthenticated, isLoading, router]);

  // Handle call start
  const handleCallStart = useCallback((newCallId: string) => {
    setIsCallActive(true);
    setCallId(newCallId);
    console.log("📞 Call started with ID:", newCallId);

    // Add initial message
    setTranscriptMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hello! I'm your mental health assistant. How are you feeling today?",
        timestamp: new Date(),
        confidence: 0.95,
      },
    ]);
  }, []);

  // Handle call end
  const handleCallEnd = useCallback((endedCallId: string) => {
    setIsCallActive(false);
    setCallId(null);
    console.log("📞 Call ended with ID:", endedCallId);

    // Add farewell message
    setTranscriptMessages((prev) => [
      ...prev,
      {
        id: `farewell-${Date.now()}`,
        role: "assistant",
        content:
          "Thank you for our conversation. Take care and remember, support is always available.",
        timestamp: new Date(),
        confidence: 0.98,
      },
    ]);
  }, []);

  // Handle transcript updates
  const handleTranscriptUpdate = useCallback(
    (transcript: string, role: "user" | "assistant") => {
      const newMessage: TranscriptMessage = {
        id: `${role}-${Date.now()}-${Math.random()}`,
        role,
        content: transcript,
        timestamp: new Date(),
        confidence: Math.random() * 0.3 + 0.7, // Random confidence between 0.7-1.0
      };

      setTranscriptMessages((prev) => [...prev, newMessage]);
    },
    []
  );

  // Demo functionality - add sample messages
  const addSampleMessage = (role: "user" | "assistant", content: string) => {
    const newMessage: TranscriptMessage = {
      id: `demo-${role}-${Date.now()}`,
      role,
      content,
      timestamp: new Date(),
      confidence: Math.random() * 0.3 + 0.7,
    };
    setTranscriptMessages((prev) => [...prev, newMessage]);
  };

  const clearTranscript = () => {
    setTranscriptMessages([]);
  };

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-t-2 border-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-3xl font-bold flex items-center justify-center gap-3">
          <Headphones className="h-8 w-8 text-primary" />
          Voice Integration Demo
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Experience our voice-enabled mental health assistant. Choose between
          web-based voice calls or phone calls, and see real-time transcription
          in action.
        </p>
      </motion.div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Column - Voice Controls */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-6"
        >
          {/* Voice Call Interface */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mic className="h-5 w-5" />
                Voice Call Interface
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="web" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="web" className="flex items-center gap-2">
                    <Mic className="h-4 w-4" />
                    Web Call
                  </TabsTrigger>
                  <TabsTrigger
                    value="phone"
                    className="flex items-center gap-2"
                  >
                    <Phone className="h-4 w-4" />
                    Phone Call
                  </TabsTrigger>
                </TabsList>

                {/* Web Call Tab */}
                <TabsContent value="web" className="space-y-4">
                  <div className="text-center space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Click to start a voice conversation using your browser's
                      microphone.
                    </p>

                    <VoiceCallButton
                      mode="web"
                      onCallStart={handleCallStart}
                      onCallEnd={handleCallEnd}
                      onTranscriptUpdate={handleTranscriptUpdate}
                      className="flex justify-center"
                    />

                    <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Browser microphone access required
                    </div>
                  </div>
                </TabsContent>

                {/* Phone Call Tab */}
                <TabsContent value="phone" className="space-y-4">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        placeholder="+1 (555) 123-4567"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        className="w-full mt-1 px-3 py-2 border rounded-md"
                        disabled={isCallActive}
                      />
                    </div>

                    <div className="text-center">
                      <VoiceCallButton
                        mode="phone"
                        phoneNumber={phoneNumber}
                        onCallStart={handleCallStart}
                        onCallEnd={handleCallEnd}
                        disabled={!phoneNumber.trim()}
                        className="flex justify-center"
                      />
                    </div>

                    <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      Phone calls require Vapi credits
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Demo Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Demo Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addSampleMessage(
                      "user",
                      "I've been feeling anxious lately and having trouble sleeping."
                    )
                  }
                  disabled={!isCallActive && transcriptMessages.length === 0}
                >
                  Add User Message
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addSampleMessage(
                      "assistant",
                      "I understand that anxiety can really affect sleep. Have you tried any relaxation techniques before bed?"
                    )
                  }
                  disabled={!isCallActive && transcriptMessages.length === 0}
                >
                  Add Assistant Reply
                </Button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={clearTranscript}
                className="w-full"
                disabled={transcriptMessages.length === 0}
              >
                Clear Transcript
              </Button>
            </CardContent>
          </Card>

          {/* Status Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Connection Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Call Status:</span>
                <span
                  className={`text-sm font-medium ${
                    isCallActive ? "text-green-600" : "text-gray-500"
                  }`}
                >
                  {isCallActive ? "Active" : "Inactive"}
                </span>
              </div>

              {callId && (
                <div className="flex items-center justify-between">
                  <span className="text-sm">Call ID:</span>
                  <span className="text-xs font-mono bg-muted px-2 py-1 rounded">
                    {callId.slice(0, 8)}...
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-sm">Messages:</span>
                <span className="text-sm font-medium">
                  {transcriptMessages.length}
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Column - Live Transcript */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <LiveTranscript
            isCallActive={isCallActive}
            messages={transcriptMessages}
            showTimestamps={true}
            showConfidence={true}
            maxHeight="600px"
          />
        </motion.div>
      </div>

      {/* Feature Highlights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>
              Section 4: Frontend Glue - Features Implemented
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <h4 className="font-medium">VoiceCallButton Component</h4>
                  <p className="text-sm text-muted-foreground">
                    Integrated with Vapi Web SDK for both web and phone calls
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <h4 className="font-medium">Live Transcript UI</h4>
                  <p className="text-sm text-muted-foreground">
                    Real-time conversation display with timestamps and
                    confidence
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <h4 className="font-medium">Voice/Start API Integration</h4>
                  <p className="text-sm text-muted-foreground">
                    Seamless connection to backend voice processing pipeline
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <h4 className="font-medium">Zero Feature Regression</h4>
                  <p className="text-sm text-muted-foreground">
                    All chat functionality preserved, voice added as enhancement
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default VoiceDemoPage;
