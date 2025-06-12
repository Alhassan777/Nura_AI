import { MemoryItem } from "../components/chat-components/types";

/**
 * Transform backend memory data to frontend format with computed properties
 */
export function transformMemoryForFrontend(backendMemory: any): MemoryItem {
  const memoryCategory =
    backendMemory.metadata?.memory_category ||
    (backendMemory.is_emotional_anchor
      ? "emotional_anchor"
      : backendMemory.storage_type || "short_term");

  return {
    ...backendMemory,
    metadata: {
      ...backendMemory.metadata,
      memory_category: memoryCategory,
    },
    // Computed properties for backwards compatibility
    is_emotional_anchor: memoryCategory === "emotional_anchor",
    storage_type:
      memoryCategory === "emotional_anchor"
        ? "long_term"
        : memoryCategory === "long_term"
        ? "long_term"
        : "short_term",
  };
}

/**
 * Transform array of backend memories to frontend format
 */
export function transformMemoriesForFrontend(
  backendMemories: any[]
): MemoryItem[] {
  return backendMemories.map(transformMemoryForFrontend);
}

/**
 * Get memory category color for UI
 */
export function getMemoryCategoryColor(category: string): string {
  switch (category) {
    case "emotional_anchor":
      return "pink";
    case "long_term":
      return "purple";
    case "short_term":
      return "blue";
    default:
      return "default";
  }
}

/**
 * Get memory category display name
 */
export function getMemoryCategoryName(category: string): string {
  switch (category) {
    case "emotional_anchor":
      return "Emotional Anchor";
    case "long_term":
      return "Long-term Memory";
    case "short_term":
      return "Short-term Memory";
    default:
      return category;
  }
}

/**
 * Check if memory matches category filter
 */
export function matchesMemoryCategory(
  memory: MemoryItem,
  categoryFilter: string | null
): boolean {
  if (!categoryFilter || categoryFilter === "all") return true;

  const memoryCategory =
    memory.metadata?.memory_category ||
    (memory.is_emotional_anchor
      ? "emotional_anchor"
      : memory.storage_type || "short_term");

  return memoryCategory === categoryFilter;
}
