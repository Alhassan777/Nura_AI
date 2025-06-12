import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// Mock API functions - these would be replaced with actual API calls
const chatHistoryApi = {
  getChatHistory: async () => {
    // Mock data with call types and transcripts
    return Array.from({ length: 10 }, (_, i) => {
      const isVoiceCall = Math.random() > 0.6; // 40% chance of voice call
      const callDuration = isVoiceCall
        ? Math.floor(Math.random() * 1800) + 300
        : null; // 5-35 minutes for voice calls

      return {
        id: `session-${i + 1}`,
        title: `${isVoiceCall ? "Voice Call" : "Text Chat"} ${i + 1}`,
        type: isVoiceCall ? "voice" : "text",
        created_at: new Date(
          Date.now() - i * 24 * 60 * 60 * 1000
        ).toISOString(),
        message_count: isVoiceCall ? null : Math.floor(Math.random() * 20) + 5,
        call_duration: callDuration,
        last_message: isVoiceCall
          ? `Voice call ended after ${Math.floor(
              (callDuration || 0) / 60
            )} minutes`
          : `This is the last message from conversation ${i + 1}`,
        crisis_detected: Math.random() > 0.8,
        action_plans_created: Math.floor(Math.random() * 3),
        wellness_checks_scheduled: Math.floor(Math.random() * 2),
        summary: isVoiceCall
          ? `Voice conversation covering emotional support and wellness check-in. Duration: ${Math.floor(
              (callDuration || 0) / 60
            )} minutes.`
          : `Text conversation ${
              i + 1
            } covering various topics and emotional support.`,
        transcript: isVoiceCall
          ? {
              available: true,
              preview:
                "User: I've been feeling really anxious lately...\nNura: I hear that you're experiencing anxiety. Can you tell me more about what's been triggering these feelings?\nUser: It's mostly work stress and some relationship issues...",
              word_count: Math.floor(Math.random() * 2000) + 500,
              confidence_score: 0.85 + Math.random() * 0.1, // 85-95% accuracy
            }
          : null,
        mood_analysis: {
          dominant_emotion: ["anxious", "sad", "hopeful", "frustrated", "calm"][
            Math.floor(Math.random() * 5)
          ],
          emotional_intensity: Math.floor(Math.random() * 10) + 1,
          improvement_noted: Math.random() > 0.5,
        },
      };
    });
  },

  getChatSession: async (sessionId: string) => {
    const isVoiceCall = sessionId.includes("voice");
    const callDuration = isVoiceCall ? 1800 : null;

    return {
      id: sessionId,
      title: `${isVoiceCall ? "Voice Call" : "Text Chat"} Details`,
      type: isVoiceCall ? "voice" : "text",
      created_at: new Date().toISOString(),
      call_duration: callDuration,
      messages: isVoiceCall
        ? []
        : [
            { role: "user", content: "Hello Nura, I need to talk to someone." },
            {
              role: "assistant",
              content: "Hello! I'm here for you. What's on your mind today?",
            },
          ],
      transcript: isVoiceCall
        ? {
            available: true,
            full_transcript: `[00:00] User: Hi Nura, I've been having a really tough day.

[00:05] Nura: I'm sorry to hear you're having a difficult day. I'm here to listen and support you. What's been making today particularly challenging for you?

[00:15] User: Well, I got into an argument with my partner this morning, and then work was just overwhelming. I feel like I can't catch a break.

[00:28] Nura: That sounds incredibly stressful - dealing with relationship tension and work pressure at the same time can feel overwhelming. It's completely understandable that you're feeling this way. Let's talk through this together.

[00:42] User: I just don't know how to handle all of this stress. Sometimes I feel like I'm drowning.

[00:48] Nura: That feeling of drowning when stress piles up is something many people experience, and it's a valid way to feel. You're not alone in this. Can we start by talking about some immediate ways to help you feel more grounded right now?

[Continue conversation...]`,
            summary:
              "User discussed relationship conflicts and work stress. Nura provided emotional support and coping strategies.",
            key_topics: [
              "relationship_conflict",
              "work_stress",
              "coping_strategies",
            ],
            crisis_moments: [],
            positive_moments: [
              "user_expressed_gratitude",
              "breakthrough_moment_at_15min",
            ],
            word_count: 2450,
            confidence_score: 0.89,
          }
        : null,
      summary: isVoiceCall
        ? `Voice call focusing on stress management and relationship support. User showed improvement during call.`
        : "Text conversation about daily challenges and emotional support.",
    };
  },

  clearChatHistory: async () => {
    return { success: true };
  },

  exportChatHistory: async () => {
    const blob = new Blob(["Chat history export data"], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "nura-chat-history.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    return { success: true };
  },

  downloadTranscript: async (sessionId: string) => {
    const session = await chatHistoryApi.getChatSession(sessionId);
    if (session.transcript) {
      const blob = new Blob([session.transcript.full_transcript], {
        type: "text/plain",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `nura-transcript-${sessionId}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
    return { success: true };
  },
};

export const useChatHistory = (limit = 50) => {
  return useQuery({
    queryKey: ["chat", "history", limit],
    queryFn: () => chatHistoryApi.getChatHistory(),
  });
};

export const useClearChatHistory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatHistoryApi.clearChatHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", "history"] });
    },
  });
};

export const useExportChatHistory = () => {
  return useMutation({
    mutationFn: chatHistoryApi.exportChatHistory,
  });
};

export const useChatSession = (sessionId: string) => {
  return useQuery({
    queryKey: ["chat", "session", sessionId],
    queryFn: () => chatHistoryApi.getChatSession(sessionId),
    enabled: !!sessionId,
  });
};
