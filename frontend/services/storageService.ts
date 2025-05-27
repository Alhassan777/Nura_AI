// Storage service for call data
// Client-side implementation using localStorage
// In a production app, this would connect to a database API

export interface CallData {
  id: string;
  userId: string;
  date: string;
  transcript?: string;
  summary?: string;
  emotionalData?: {
    body_locus?: string;
    scene_title?: string;
    sketch_shape?: string;
    temporal_tag?: "new" | "familiar";
    color_palette?: string[];
    sketch_motion?: string;
    cognitive_load?: string;
    ground_emotion?: string;
    metaphor_prompt?: string;
    temp_descriptor?: string;
    scene_description?: string;
    texture_descriptor?: string;
  };
  generatedImageUrl?: string;
}

// Client-side storage implementation
export class ClientStorageService {
  private static STORAGE_KEY = "nura_calls";

  static getCalls(userId: string): CallData[] {
    if (typeof window === "undefined") return [];

    const storedData = localStorage.getItem(this.STORAGE_KEY);
    if (!storedData) return [];

    try {
      const allCalls = JSON.parse(storedData) as CallData[];
      return allCalls.filter((call) => call.userId === userId);
    } catch (error) {
      console.error("Failed to parse stored calls:", error);
      return [];
    }
  }

  static saveCall(callData: CallData): void {
    if (typeof window === "undefined") return;

    const storedData = localStorage.getItem(this.STORAGE_KEY);
    let calls: CallData[] = [];

    if (storedData) {
      try {
        calls = JSON.parse(storedData);
        // Replace if exists, otherwise add new
        const index = calls.findIndex((c) => c.id === callData.id);
        if (index >= 0) {
          calls[index] = callData;
        } else {
          calls.push(callData);
        }
      } catch (error) {
        console.error("Failed to parse stored calls:", error);
        calls = [callData];
      }
    } else {
      calls = [callData];
    }

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(calls));
  }

  static getCall(callId: string): CallData | null {
    if (typeof window === "undefined") return null;

    const storedData = localStorage.getItem(this.STORAGE_KEY);
    if (!storedData) return null;

    try {
      const calls = JSON.parse(storedData) as CallData[];
      return calls.find((call) => call.id === callId) || null;
    } catch (error) {
      console.error("Failed to parse stored calls:", error);
      return null;
    }
  }

  // Additional method to clear all calls (useful for testing)
  static clearAllCalls(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(this.STORAGE_KEY);
  }

  // Method to get call count for a user
  static getCallCount(userId: string): number {
    return this.getCalls(userId).length;
  }
}
