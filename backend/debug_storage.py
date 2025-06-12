#!/usr/bin/env python3
"""
Debug script to understand storage decisions
"""
import asyncio
from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem
from utils.scoring.gemini_scorer import GeminiScorer
from datetime import datetime


async def debug_storage_decision():
    print("🔍 Debugging storage decision process...")

    # Test memory
    test_memory = "My young brother died today"

    # Create memory item
    memory = MemoryItem(
        id="test-123",
        content=test_memory,
        type="chat",
        metadata={},
        timestamp=datetime.utcnow(),
    )

    # Score it with Gemini
    scorer = GeminiScorer()
    scores = scorer.score_memory(memory)

    print(f"\n📊 Gemini Scorer Results:")
    for i, score in enumerate(scores):
        print(f"  Component {i}:")
        print(f"    Relevance: {score.relevance}")
        print(f"    Stability: {score.stability}")
        print(f"    Explicitness: {score.explicitness}")
        print(f"    Metadata:")
        for key, value in score.metadata.items():
            print(f"      {key}: {value}")
        print()

    # Test storage decision logic
    if scores:
        score = scores[0]
        metadata = score.metadata

        memory_nature = metadata.get("memory_nature", "passing_moment")
        story_significance = metadata.get("story_significance", "daily_rhythm")
        emotional_resonance = metadata.get("emotional_resonance", "surface")
        keep_or_release = metadata.get("keep_or_release", "naturally_fade")

        print(f"🎯 Storage Decision Inputs:")
        print(f"  memory_nature: {memory_nature}")
        print(f"  story_significance: {story_significance}")
        print(f"  emotional_resonance: {emotional_resonance}")
        print(f"  keep_or_release: {keep_or_release}")

        # Test the decision logic
        from services.memory.storage_processor import StorageProcessor

        storage_processor = StorageProcessor(None, None, None, None)

        should_store = storage_processor._should_treasure_long_term(
            memory_nature, story_significance, emotional_resonance, keep_or_release
        )

        print(f"\n✅ Storage Decision: {should_store}")

        # Test classification
        category = storage_processor._classify_memory_simple(
            memory_nature, story_significance, emotional_resonance
        )

        print(f"📂 Memory Category: {category}")


asyncio.run(debug_storage_decision())
