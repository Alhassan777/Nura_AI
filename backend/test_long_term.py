#!/usr/bin/env python3
"""
Test long-term storage decision
"""
import asyncio
from services.memory.memoryService import MemoryService


async def test_storage_decision():
    memory_service = MemoryService()

    # Test memory that should be long-term
    test_memory = "My young brother died today. I am heartbroken and this will stay with me forever."
    user_id = "test-user-456"

    print("Testing storage decision for meaningful memory...")
    result = await memory_service.process_memory(
        user_id=user_id, content=test_memory, type="chat"
    )

    print(f'Storage result: {result.get("storage_details", {})}')

    # Check what's in stores
    regular = await memory_service.get_regular_memories(user_id)
    anchors = await memory_service.get_emotional_anchors(user_id)

    print(f"Found {len(regular)} regular memories, {len(anchors)} anchors")
    for mem in regular + anchors:
        print(f'  - {mem.metadata.get("memory_category")}: {mem.content[:50]}')


asyncio.run(test_storage_decision())
