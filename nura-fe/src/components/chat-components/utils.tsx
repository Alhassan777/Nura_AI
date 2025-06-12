import { SendMessageBody } from "@/services/apis";
import { MemoryStats } from "./types";

import { MemoryContext, MemoryItem } from "./types";
import {
  Heart,
  Clock,
  Database,
  Trash2,
  Lock,
  CheckCircle,
} from "lucide-react";
import { axiosInstance } from "../../services/apis";
import { transformMemoriesForFrontend } from "../../utils/memoryUtils";

export const getCrisisLevelBadgeStatus = (
  level: string
): "error" | "warning" | "success" | "processing" | "default" => {
  switch (level) {
    case "CRISIS":
      return "error";
    case "CONCERN":
      return "warning";
    case "SUPPORT":
      return "success";
    default:
      return "default";
  }
};

export const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};

export const getRiskBadgeStatus = (
  riskLevel: string
): "error" | "warning" | "success" | "default" => {
  switch (riskLevel) {
    case "high":
      return "error";
    case "medium":
      return "warning";
    case "low":
      return "success";
    default:
      return "default";
  }
};

export const getStorageIcon = (storageType: string, isAnchor?: boolean) => {
  if (isAnchor) return <Heart className="w-4 h-4 text-pink-500" />;
  if (storageType === "short_term")
    return <Clock className="w-4 h-4 text-blue-500" />;
  return <Database className="w-4 h-4 text-purple-500" />;
};

export const getChoiceIcon = (choice: string) => {
  switch (choice) {
    case "remove_entirely":
      return <Trash2 className="w-4 h-4" />;
    case "remove_pii_only":
      return <Lock className="w-4 h-4" />;
    case "keep_original":
      return <CheckCircle className="w-4 h-4" />;
    default:
      return null;
  }
};

export const getChoiceButtonType = (
  currentChoice: string,
  buttonKey: string
): "primary" | "default" | "dashed" => {
  if (currentChoice === buttonKey) {
    if (buttonKey === "remove_entirely") return "primary";
    if (buttonKey === "remove_pii_only") return "primary";
    if (buttonKey === "keep_original") return "primary";
  }
  return "default";
};

export const fetchAllMemories = async (): Promise<MemoryContext> => {
  try {
    const response = await axiosInstance.get("/memory/all-long-term");
    const data = response.data;

    // Transform backend data to frontend format
    const emotionalAnchors = transformMemoriesForFrontend(
      data.emotional_anchors || []
    );
    const regularMemories = transformMemoriesForFrontend(
      data.regular_memories || []
    );

    return {
      short_term: [], // Short-term memories are not included in all-long-term endpoint
      long_term: regularMemories,
      emotional_anchors: emotionalAnchors,
      digest: `Found ${emotionalAnchors.length} emotional anchors and ${regularMemories.length} regular memories.`,
    };
  } catch (error) {
    console.error("Error fetching memories:", error);
    return {
      short_term: [],
      long_term: [],
      emotional_anchors: [],
      digest: "Unable to load memories. Please try again.",
    };
  }
};

export const fetchMemoryContext = async (): Promise<MemoryContext> => {
  try {
    const response = await axiosInstance.post("/memory/context");
    const context = response.data.context;

    // Transform backend data to frontend format
    const shortTerm = transformMemoriesForFrontend(context.short_term || []);
    const longTerm = transformMemoriesForFrontend(context.long_term || []);

    // Extract emotional anchors from long-term memories
    const emotionalAnchors = longTerm.filter(
      (memory) => memory.metadata?.memory_category === "emotional_anchor"
    );

    // Regular long-term memories (excluding emotional anchors)
    const regularLongTerm = longTerm.filter(
      (memory) => memory.metadata?.memory_category === "long_term"
    );

    return {
      short_term: shortTerm,
      long_term: regularLongTerm,
      emotional_anchors: emotionalAnchors,
      digest: context.digest || "Memory context loaded successfully.",
    };
  } catch (error) {
    console.error("Error fetching memory context:", error);
    return {
      short_term: [],
      long_term: [],
      emotional_anchors: [],
      digest: "Unable to load memory context. Please try again.",
    };
  }
};
