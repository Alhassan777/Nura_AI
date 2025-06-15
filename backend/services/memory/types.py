from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class MemoryItem:
    id: str
    content: str
    type: str
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

    @property
    def user_id(self) -> Optional[str]:
        """Get user_id from metadata for consistency with storage systems."""
        return self.metadata.get("user_id")


@dataclass
class MemoryScore:
    relevance: float
    stability: float
    explicitness: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemoryContext:
    short_term: List[MemoryItem]
    long_term: List[MemoryItem]
    digest: str

    # Backward compatibility properties
    @property
    def short_term_memories(self) -> List[MemoryItem]:
        return self.short_term

    @property
    def long_term_memories(self) -> List[MemoryItem]:
        return self.long_term

    @property
    def summary(self) -> str:
        return self.digest


@dataclass
class MemoryConfig:
    short_term_size: int
    long_term_size: int
    relevance_threshold: float
    stability_threshold: float
    explicitness_threshold: float
    min_score_threshold: float


@dataclass
class MemoryStats:
    total: int
    short_term: int
    long_term: int
    sensitive: int
    emotional_anchors: int = 0
    categories: Optional[Dict[str, int]] = None
    recent_activity: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.categories is None:
            self.categories = {
                "short_term": self.short_term,
                "long_term": self.long_term,
                "emotional_anchor": self.emotional_anchors,
            }

        if self.recent_activity is None:
            self.recent_activity = {
                "memories_added_today": 0,
                "memories_added_this_week": 0,
                "last_memory_timestamp": None,
            }

    # Backward compatibility properties
    @property
    def redis_count(self) -> int:
        return self.short_term

    @property
    def vector_count(self) -> int:
        return self.long_term

    @property
    def regular_memories(self) -> int:
        # This would be long_term minus emotional_anchors
        return self.long_term - self.emotional_anchors
