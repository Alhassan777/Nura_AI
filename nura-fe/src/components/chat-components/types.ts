export interface ChatMessage {
  id: string;
  message: string;
  response: string;
  crisis_level: string;
  crisis_explanation: string;
  resources_provided: string[];
  coping_strategies: string[];
  memory_stored: boolean;
  timestamp: string;
  configuration_warning?: boolean;
  error?: string;
  isUserMessage?: boolean; // Flag to identify messages waiting for response
}

export interface HealthStatus {
  status: string;
  memory_service?: any;
  error?: string;
  timestamp: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  metadata: {
    // Simplified memory classification
    memory_category?: "short_term" | "long_term" | "emotional_anchor";
    is_meaningful?: boolean;
    is_lasting?: boolean;
    is_symbolic?: boolean;
    storage_type?: string;
    // Legacy compatibility
    has_pii?: boolean;
    detected_items?: string[];
    score?: {
      relevance: number;
      stability: number;
      explicitness: number;
    };
    [key: string]: any;
  };
  // Computed properties for compatibility
  is_emotional_anchor?: boolean; // Computed from memory_category === "emotional_anchor"
  storage_type?: "short_term" | "long_term"; // Computed from memory_category
}

export interface MemoryStats {
  total: number;
  short_term: number;
  long_term: number;
  sensitive: number;
  emotional_anchors?: number; // New field for emotional anchors count
}

export interface MemoryContext {
  short_term: MemoryItem[];
  long_term: MemoryItem[];
  emotional_anchors?: MemoryItem[];
  digest: string;
}

export interface PIIItem {
  id: string;
  text: string;
  type: string;
  risk_level: "high" | "medium" | "low";
  description: string;
  confidence: number;
}

export interface MemoryWithPII {
  id: string;
  content: string;
  type: string;
  storage_type: "short_term" | "long_term";
  timestamp: string;
  memory_category: "short_term" | "long_term" | "emotional_anchor";
  is_meaningful?: boolean;
  is_lasting?: boolean;
  is_symbolic?: boolean;
  pii_detected: PIIItem[];
  pii_summary: {
    types: string[];
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
  };
}

export interface PrivacyOption {
  label: string;
  description: string;
  icon: string;
}

export interface PrivacyReviewData {
  memories_with_pii: MemoryWithPII[];
  total_count: number;
  privacy_options: {
    remove_entirely: PrivacyOption;
    remove_pii_only: PrivacyOption;
    keep_original: PrivacyOption;
  };
}
