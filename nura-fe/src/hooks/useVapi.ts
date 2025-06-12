import { useState, useEffect, useRef, useCallback } from "react";
import Vapi from "@vapi-ai/web";
import { voiceApi } from "@/services/apis/voice";

export interface VapiState {
  isConnected: boolean;
  isCallActive: boolean;
  isLoading: boolean;
  isMuted: boolean;
  isAssistantSpeaking: boolean;
  audioLevel: number;
  callDuration: number;
  error: string | null;
  transcript: string;
  callId?: string;
}

export interface VapiMessage {
  type: string;
  role?: "user" | "assistant" | "system";
  transcript?: string;
  message?: any;
}

export interface UseVapiOptions {
  assistantId?: string;
  onCallStart?: () => void;
  onCallEnd?: () => void;
  onMessage?: (message: VapiMessage) => void;
  onError?: (error: string) => void;
}

export const useVapi = (options: UseVapiOptions = {}) => {
  const {
    assistantId = process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID || "",
    onCallStart,
    onCallEnd,
    onMessage,
    onError,
  } = options;

  const [state, setState] = useState<VapiState>({
    isConnected: false,
    isCallActive: false,
    isLoading: false,
    isMuted: false,
    isAssistantSpeaking: false,
    audioLevel: 0,
    callDuration: 0,
    error: null,
    transcript: "",
  });

  const vapiRef = useRef<Vapi | null>(null);
  const callStartTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize Vapi instance
  const initializeVapi = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Get configuration from backend
      const callConfig = await voiceApi.initiateBrowserCall({
        assistant_id: assistantId,
        metadata: {
          timestamp: new Date().toISOString(),
          channel: "web",
        },
      });

      // Initialize Vapi with public key
      vapiRef.current = new Vapi(callConfig.publicKey);

      // Set up event listeners
      setupEventListeners();

      setState((prev) => ({
        ...prev,
        isLoading: false,
        isConnected: true,
        callId: callConfig.metadata.callId,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to initialize voice connection";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [assistantId, onError]);

  // Set up Vapi event listeners
  const setupEventListeners = useCallback(() => {
    const vapi = vapiRef.current;
    if (!vapi) return;

    // Call lifecycle events
    vapi.on("call-start", () => {
      callStartTimeRef.current = Date.now();
      startDurationTimer();
      setState((prev) => ({
        ...prev,
        isCallActive: true,
        isLoading: false,
      }));
      onCallStart?.();
    });

    vapi.on("call-end", () => {
      stopDurationTimer();
      setState((prev) => ({
        ...prev,
        isCallActive: false,
        isAssistantSpeaking: false,
        callDuration: 0,
      }));
      onCallEnd?.();
    });

    // Speech events
    vapi.on("speech-start", () => {
      setState((prev) => ({ ...prev, isAssistantSpeaking: true }));
    });

    vapi.on("speech-end", () => {
      setState((prev) => ({ ...prev, isAssistantSpeaking: false }));
    });

    // Volume level monitoring
    vapi.on("volume-level", (volume: number) => {
      setState((prev) => ({
        ...prev,
        audioLevel: Math.min(100, volume * 100),
      }));
    });

    // Message handling (transcripts, function calls, etc.)
    vapi.on("message", (message: any) => {
      const vapiMessage: VapiMessage = {
        type: message.type,
        role: message.role,
        transcript: message.transcript,
        message,
      };

      // Update transcript for display
      if (message.type === "transcript" && message.transcript) {
        setState((prev) => ({
          ...prev,
          transcript: `${message.role === "user" ? "You" : "Nura"}: ${
            message.transcript
          }`,
        }));
      }

      onMessage?.(vapiMessage);
    });

    // Error handling
    vapi.on("error", (error: any) => {
      const errorMessage = error?.message || "Voice connection error";
      setState((prev) => ({ ...prev, error: errorMessage }));
      onError?.(errorMessage);
    });
  }, [onCallStart, onCallEnd, onMessage, onError]);

  // Start call duration timer
  const startDurationTimer = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    durationIntervalRef.current = setInterval(() => {
      const duration = Math.floor(
        (Date.now() - callStartTimeRef.current) / 1000
      );
      setState((prev) => ({ ...prev, callDuration: duration }));
    }, 1000);
  }, []);

  // Stop call duration timer
  const stopDurationTimer = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
  }, []);

  // Start voice call
  const startCall = useCallback(async () => {
    if (!vapiRef.current || state.isCallActive) return;

    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Start call with assistant ID and metadata
      await vapiRef.current.start(assistantId, {
        metadata: {
          userId: "current-user", // This will be populated by JWT auth
          timestamp: new Date().toISOString(),
          channel: "web",
        },
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to start call";
      setState((prev) => ({ ...prev, isLoading: false, error: errorMessage }));
      onError?.(errorMessage);
    }
  }, [assistantId, state.isCallActive, onError]);

  // End voice call
  const endCall = useCallback(async () => {
    if (!vapiRef.current || !state.isCallActive) return;

    try {
      await vapiRef.current.stop();

      // Optionally notify backend about call end
      if (state.callId) {
        await voiceApi.endCall(state.callId);
      }
    } catch (error) {
      console.error("Error ending call:", error);
    }
  }, [state.isCallActive, state.callId]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (!vapiRef.current) return;

    const newMutedState = !state.isMuted;
    vapiRef.current.setMuted(newMutedState);
    setState((prev) => ({ ...prev, isMuted: newMutedState }));
  }, [state.isMuted]);

  // Send text message to assistant
  const sendMessage = useCallback(
    (message: string, role: "user" | "system" = "user") => {
      if (!vapiRef.current || !state.isCallActive) return;

      vapiRef.current.send({
        type: "add-message",
        message: {
          role,
          content: message,
        },
      });
    },
    [state.isCallActive]
  );

  // Make assistant say something
  const say = useCallback(
    (message: string, endCallAfter = false) => {
      if (!vapiRef.current || !state.isCallActive) return;

      vapiRef.current.say(message, endCallAfter);
    },
    [state.isCallActive]
  );

  // Format call duration for display
  const formatDuration = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopDurationTimer();
      if (vapiRef.current) {
        try {
          vapiRef.current.stop();
        } catch (error) {
          console.error("Error stopping Vapi:", error);
        }
      }
    };
  }, [stopDurationTimer]);

  return {
    state,
    actions: {
      initializeVapi,
      startCall,
      endCall,
      toggleMute,
      sendMessage,
      say,
    },
    utils: {
      formatDuration,
      isInitialized: !!vapiRef.current,
    },
  };
};
