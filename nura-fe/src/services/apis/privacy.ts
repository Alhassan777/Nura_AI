import { axiosInstance } from "./index";

export interface PIIAnalysisResult {
  detected_pii: {
    text: string;
    type: string;
    risk_level: "high" | "medium" | "low";
    confidence: number;
    start_pos: number;
    end_pos: number;
  }[];
  risk_summary: {
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
    total_detected: number;
  };
  sanitized_text?: string;
  recommendations: string[];
}

export interface PrivacySettings {
  pii_detection_enabled: boolean;
  data_retention_days: number;
  auto_sanitize_pii: boolean;
  allowed_pii_types: string[];
  notification_preferences: {
    pii_detected: boolean;
    data_retention_reminder: boolean;
  };
}

export interface DataRetentionReport {
  total_memories: number;
  memories_to_delete: number;
  deletion_date: string;
  categories: {
    short_term: number;
    long_term: number;
    emotional_anchors: number;
  };
}

// Privacy API functions
export const privacyApi = {
  // Analyze text for PII
  analyzeText: (text: string) =>
    axiosInstance
      .post("/privacy/analyze", { text })
      .then((res) => res.data) as Promise<PIIAnalysisResult>,

  // Get current privacy settings
  getSettings: () =>
    axiosInstance
      .get("/privacy/settings")
      .then((res) => res.data) as Promise<PrivacySettings>,

  // Update privacy settings
  updateSettings: (settings: Partial<PrivacySettings>) =>
    axiosInstance.put("/privacy/settings", settings).then((res) => res.data),

  // Get data retention report
  getDataRetentionReport: () =>
    axiosInstance
      .get("/privacy/data-retention-report")
      .then((res) => res.data) as Promise<DataRetentionReport>,

  // Request data deletion
  requestDataDeletion: (categories: string[]) =>
    axiosInstance
      .post("/privacy/request-deletion", { categories })
      .then((res) => res.data),

  // Get privacy audit log
  getAuditLog: (limit = 50) =>
    axiosInstance
      .get(`/privacy/audit-log?limit=${limit}`)
      .then((res) => res.data),

  // Export user data
  exportUserData: () =>
    axiosInstance
      .get("/privacy/export-data", {
        responseType: "blob",
      })
      .then((res) => res.data),
};
