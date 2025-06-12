import asyncio
from utils.scoring.gemini_scorer import GeminiScorer
from services.memory.types import MemoryItem
from datetime import datetime, timezone


def test_gemini():
    scorer = GeminiScorer()

    # Test 1: Long-term memory
    print("=== TESTING LONG-TERM MEMORY ===")
    memory1 = MemoryItem(
        id="test1",
        content="My young brother died today",
        type="conversation_turn",
        metadata={"test_mode": True},
        timestamp=datetime.now(timezone.utc),
    )

    scores1 = scorer.score_memory(memory1)
    for i, score in enumerate(scores1):
        print(
            f'Component {i+1}: category={score.metadata.get("memory_category")}, meaningful={score.metadata.get("is_meaningful")}, lasting={score.metadata.get("is_lasting")}, symbolic={score.metadata.get("is_symbolic")}'
        )

    # Test 2: Emotional anchor
    print("\n=== TESTING EMOTIONAL ANCHOR ===")
    memory2 = MemoryItem(
        id="test2",
        content="The old oak tree in the park makes me feel connected to something bigger when I sit under it",
        type="conversation_turn",
        metadata={"test_mode": True},
        timestamp=datetime.now(timezone.utc),
    )

    scores2 = scorer.score_memory(memory2)
    for i, score in enumerate(scores2):
        print(
            f'Component {i+1}: category={score.metadata.get("memory_category")}, meaningful={score.metadata.get("is_meaningful")}, lasting={score.metadata.get("is_lasting")}, symbolic={score.metadata.get("is_symbolic")}'
        )

    # Test 3: Short-term memory
    print("\n=== TESTING SHORT-TERM MEMORY ===")
    memory3 = MemoryItem(
        id="test3",
        content="I feel stressed about work today",
        type="conversation_turn",
        metadata={"test_mode": True},
        timestamp=datetime.now(timezone.utc),
    )

    scores3 = scorer.score_memory(memory3)
    for i, score in enumerate(scores3):
        print(
            f'Component {i+1}: category={score.metadata.get("memory_category")}, meaningful={score.metadata.get("is_meaningful")}, lasting={score.metadata.get("is_lasting")}, symbolic={score.metadata.get("is_symbolic")}'
        )


if __name__ == "__main__":
    test_gemini()
