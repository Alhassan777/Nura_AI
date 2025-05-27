"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Phone, PhoneOff, Loader2 } from "lucide-react";
import { useVoiceAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

// Import Vapi Web SDK
let Vapi: any;
if (typeof window !== "undefined") {
  import("@vapi-ai/web").then((module) => {
    Vapi = module.default;
  });
}

interface VoiceCallButtonProps {
  mode?: "web" | "phone";
  phoneNumber?: string;
  onCallStart?: (callId: string) => void;
  onCallEnd?: (callId: string) => void;
  onTranscriptUpdate?: (transcript: string, role: "user" | "assistant") => void;
  className?: string;
  disabled?: boolean;
}

interface CallState {
  isConnecting: boolean;
  isActive: boolean;
  callId: string | null;
  error: string | null;
  volume: number;
  isMuted: boolean;
}

const VoiceCallButton: React.FC<VoiceCallButtonProps> = ({
  mode = "web",
  phoneNumber,
  onCallStart,
  onCallEnd,
  onTranscriptUpdate,
  className = "",
  disabled = false,
}) => {
  const { user } = useVoiceAuth();
  const [vapi, setVapi] = useState<any>(null);
  const [callState, setCallState] = useState<CallState>({
    isConnecting: false,
    isActive: false,
    callId: null,
    error: null,
    volume: 0,
    isMuted: false,
  });

  // Initialize Vapi instance
  useEffect(() => {
    if (typeof window !== "undefined" && Vapi) {
      const vapiInstance = new Vapi(process.env.NEXT_PUBLIC_VAPI_WEB_KEY);
      setVapi(vapiInstance);

      // Set up event listeners
      vapiInstance.on("call-start", (call: any) => {
        console.log("📞 Call started:", call);
        setCallState((prev) => ({
          ...prev,
          isConnecting: false,
          isActive: true,
          callId: call.id,
          error: null,
        }));
        onCallStart?.(call.id);
        toast.success("Voice call connected!");
      });

      vapiInstance.on("call-end", (call: any) => {
        console.log("📞 Call ended:", call);
        setCallState((prev) => ({
          ...prev,
          isConnecting: false,
          isActive: false,
          callId: null,
          volume: 0,
          isMuted: false,
        }));
        onCallEnd?.(call.id);
        toast.info("Voice call ended");
      });

      vapiInstance.on("speech-start", () => {
        console.log("🎙️ User started speaking");
      });

      vapiInstance.on("speech-end", () => {
        console.log("🎙️ User stopped speaking");
      });

      vapiInstance.on("volume-level", (volume: number) => {
        setCallState((prev) => ({ ...prev, volume }));
      });

      vapiInstance.on("message", (message: any) => {
        console.log("💬 Message received:", message);
        if (message.type === "transcript" && onTranscriptUpdate) {
          onTranscriptUpdate(message.transcript, message.role);
        }
      });

      vapiInstance.on("error", (error: any) => {
        console.error("❌ Vapi error:", error);
        setCallState((prev) => ({
          ...prev,
          isConnecting: false,
          isActive: false,
          error: error.message || "Voice call failed",
        }));
        toast.error(`Voice call error: ${error.message || "Unknown error"}`);
      });

      return () => {
        if (vapiInstance.isSessionActive()) {
          vapiInstance.stop();
        }
      };
    }
  }, [onCallStart, onCallEnd, onTranscriptUpdate]);

  const startCall = useCallback(async () => {
    if (!vapi || callState.isConnecting || callState.isActive) return;

    try {
      setCallState((prev) => ({ ...prev, isConnecting: true, error: null }));

      // Get customerId from authenticated user
      const customerId = user?.id || user?.sub;

      if (!customerId) {
        toast.error("Please log in to start a voice call");
        setCallState((prev) => ({ ...prev, isConnecting: false }));
        return;
      }

      if (mode === "web") {
        // Web mode: Get start payload and use Vapi Web SDK
        const response = await fetch(
          `/api/voice/start?mode=web&customerId=${customerId}`
        );

        if (!response.ok) {
          throw new Error("Failed to get voice start payload");
        }

        const { startPayload } = await response.json();

        // Store the call mapping before starting
        await storeCallMapping(customerId);

        // Start the call with Vapi Web SDK
        await vapi.start(startPayload);
      } else if (mode === "phone" && phoneNumber) {
        // Phone mode: Trigger server-side call
        const response = await fetch("/api/voice/start", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            mode: "phone",
            phoneNumber,
            customerId,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to initiate phone call");
        }

        const { callId } = await response.json();

        setCallState((prev) => ({
          ...prev,
          isConnecting: false,
          isActive: true,
          callId,
        }));

        onCallStart?.(callId);
        toast.success("Phone call initiated!");
      }
    } catch (error) {
      console.error("Failed to start call:", error);
      setCallState((prev) => ({
        ...prev,
        isConnecting: false,
        error: error instanceof Error ? error.message : "Failed to start call",
      }));
      toast.error("Failed to start voice call");
    }
  }, [vapi, callState, mode, phoneNumber, user]);

  const endCall = useCallback(async () => {
    if (!vapi || !callState.isActive) return;

    try {
      if (mode === "web" && vapi.isSessionActive()) {
        await vapi.stop();
      }
      // For phone mode, the call ends on the phone side
    } catch (error) {
      console.error("Failed to end call:", error);
      toast.error("Failed to end call properly");
    }
  }, [vapi, callState.isActive, mode]);

  const toggleMute = useCallback(async () => {
    if (!vapi || !callState.isActive) return;

    try {
      if (callState.isMuted) {
        await vapi.unmute();
      } else {
        await vapi.mute();
      }
      setCallState((prev) => ({ ...prev, isMuted: !prev.isMuted }));
    } catch (error) {
      console.error("Failed to toggle mute:", error);
      toast.error("Failed to toggle mute");
    }
  }, [vapi, callState.isActive, callState.isMuted]);

  const storeCallMapping = async (customerId: string) => {
    // For web calls, we need to store the mapping after the call starts
    // This is handled in the Vapi event listeners
    try {
      // Pre-store mapping for web calls with a temporary ID
      // The actual call ID will be updated when the call starts
      const tempCallId = `web-${Date.now()}`;
      await fetch("/api/voice/mapping", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          callId: tempCallId,
          customerId,
          mode: "web",
        }),
      });
    } catch (error) {
      console.warn("Failed to pre-store call mapping:", error);
    }
  };

  const handleMainAction = () => {
    if (callState.isActive) {
      endCall();
    } else {
      startCall();
    }
  };

  const getButtonState = () => {
    if (disabled) return "disabled";
    if (callState.isConnecting) return "connecting";
    if (callState.isActive) return "active";
    return "idle";
  };

  const buttonState = getButtonState();
  const volumeSize = Math.max(60, Math.min(120, callState.volume * 100)) + "px";

  return (
    <div className={`relative flex flex-col items-center gap-4 ${className}`}>
      {/* Volume visualization */}
      <AnimatePresence>
        {callState.isActive && callState.volume > 0.1 && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
            }}
            className="absolute rounded-full bg-primary/20 dark:bg-primary/30 backdrop-blur-sm pointer-events-none"
            style={{
              width: volumeSize,
              height: volumeSize,
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              zIndex: 0,
            }}
          />
        )}
      </AnimatePresence>

      {/* Main call button */}
      <motion.div
        whileHover={!disabled ? { scale: 1.05 } : {}}
        whileTap={!disabled ? { scale: 0.95 } : {}}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        className="relative z-10"
      >
        <Button
          variant={buttonState === "active" ? "destructive" : "default"}
          size="lg"
          className={`
            rounded-full w-16 h-16 transition-all duration-300 shadow-lg relative
            ${
              buttonState === "active"
                ? "bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700"
                : "bg-primary hover:bg-primary/90"
            }
            ${
              buttonState === "connecting"
                ? "bg-yellow-500 dark:bg-yellow-600"
                : ""
            }
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
          onClick={handleMainAction}
          disabled={disabled || buttonState === "connecting"}
          aria-label={
            buttonState === "active"
              ? "End call"
              : buttonState === "connecting"
              ? "Connecting..."
              : "Start call"
          }
        >
          <motion.div
            animate={
              buttonState === "connecting"
                ? { rotate: 360 }
                : buttonState === "active"
                ? { scale: [1, 1.1, 1] }
                : { scale: 1 }
            }
            transition={{
              duration: buttonState === "connecting" ? 1 : 0.5,
              repeat:
                buttonState === "connecting" || buttonState === "active"
                  ? Infinity
                  : 0,
            }}
          >
            {buttonState === "connecting" ? (
              <Loader2 className="h-6 w-6" />
            ) : buttonState === "active" ? (
              mode === "web" ? (
                <MicOff className="h-6 w-6" />
              ) : (
                <PhoneOff className="h-6 w-6" />
              )
            ) : mode === "web" ? (
              <Mic className="h-6 w-6" />
            ) : (
              <Phone className="h-6 w-6" />
            )}
          </motion.div>
        </Button>
      </motion.div>

      {/* Mute button for web calls */}
      {mode === "web" && callState.isActive && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          className="flex gap-2"
        >
          <Button
            variant="outline"
            size="sm"
            className={`rounded-full w-10 h-10 ${
              callState.isMuted ? "bg-red-100 dark:bg-red-900" : ""
            }`}
            onClick={toggleMute}
            aria-label={callState.isMuted ? "Unmute" : "Mute"}
          >
            {callState.isMuted ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>
        </motion.div>
      )}

      {/* Status text */}
      <div className="text-center">
        <p className="text-sm font-medium">
          {buttonState === "connecting" && "Connecting..."}
          {buttonState === "active" &&
            (mode === "web" ? "Voice Call Active" : "Phone Call Active")}
          {buttonState === "idle" &&
            (mode === "web" ? "Start Voice Call" : "Start Phone Call")}
          {buttonState === "disabled" && "Voice Unavailable"}
        </p>

        {callState.error && (
          <p className="text-xs text-red-500 dark:text-red-400 mt-1">
            {callState.error}
          </p>
        )}

        {callState.isActive && callState.isMuted && (
          <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
            Microphone muted
          </p>
        )}
      </div>
    </div>
  );
};

export default VoiceCallButton;
