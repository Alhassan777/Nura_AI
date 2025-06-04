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
