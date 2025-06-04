#!/usr/bin/env python3
"""
Privacy and Data Isolation Test for Memory Retrieval Systems

This test verifies that:
1. Redis short-term memory properly isolates user data
2. Vector storage (Pinecone/Chroma) properly isolates user data
3. No cross-user data leakage occurs in either system
4. Queries only return data for the authenticated user

CRITICAL: This test validates core privacy requirements.
"""

import asyncio
import json
import logging
import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

# Import our memory systems
from services.memory.storage.redis_store import RedisStore
from services.memory.storage.vector_store import VectorStore
from services.memory.types import MemoryItem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrivacyRetrievalTest:
    """Comprehensive test for memory system privacy and data isolation."""

    def __init__(self):
        self.redis_store = RedisStore()
        self.vector_store = VectorStore()
        self.test_users = []
        self.test_memories = {}

    async def setup(self):
        """Initialize storage systems and create test data."""
        logger.info("Setting up privacy retrieval test...")

        try:
            # Initialize storage systems
            await self.redis_store.initialize()
            await self.vector_store.initialize()

            # Create test users
            self.test_users = [
                f"test_user_{i}_{uuid.uuid4().hex[:8]}" for i in range(3)
            ]

            # Create unique memories for each user
            await self._create_test_memories()

            logger.info(f"Created test data for {len(self.test_users)} users")

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    async def _create_test_memories(self):
        """Create unique test memories for each user."""
        for user_id in self.test_users:
            user_memories = []

            # Create 5 unique memories per user with distinct content
            for i in range(5):
                memory_id = f"memory_{user_id}_{i}_{uuid.uuid4().hex[:8]}"

                # Create metadata with user_id (not userId)
                metadata = {
                    "user_id": user_id,  # This is the key field for storage systems
                    "privacy_level": "high",
                    "category": f"personal_category_{i}",
                    "sensitive": True,
                    "unique_identifier": f"{user_id}_unique_{i}",
                }

                memory = MemoryItem(
                    id=memory_id,
                    content=f"Secret information for {user_id}: Personal data item {i+1}. "
                    f"This contains private details like SSN-{user_id[-4:]}-{i:04d}, "
                    f"bank account {user_id[-6:]}{i:03d}, and confidential note {i+1}.",
                    type=f"personal_data_{i}",
                    timestamp=datetime.now() + timedelta(minutes=i),
                    metadata=metadata,
                )
                user_memories.append(memory)

                # Store in both Redis and Vector store
                try:
                    redis_success = await self.redis_store.store_memory(user_id, memory)
                    vector_success = await self.vector_store.store_memory(
                        user_id, memory
                    )

                    if not redis_success:
                        logger.warning(
                            f"Failed to store memory {memory_id} in Redis for user {user_id}"
                        )
                    if not vector_success:
                        logger.warning(
                            f"Failed to store memory {memory_id} in Vector store for user {user_id}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error storing memory {memory_id} for user {user_id}: {e}"
                    )

            self.test_memories[user_id] = user_memories
            logger.info(f"Created {len(user_memories)} memories for user {user_id}")

    async def test_redis_isolation(self) -> Dict[str, Any]:
        """Test Redis data isolation between users."""
        logger.info("Testing Redis data isolation...")

        results = {
            "test_name": "Redis Data Isolation",
            "passed": True,
            "issues": [],
            "user_data_counts": {},
            "cross_contamination": [],
        }

        try:
            for user_id in self.test_users:
                # Get memories for this user
                user_memories = await self.redis_store.get_user_memories(user_id)
                results["user_data_counts"][user_id] = len(user_memories)

                # Verify all memories belong to this user
                for memory in user_memories:
                    # Check metadata user_id
                    memory_user_id = memory.user_id  # Use the property
                    if memory_user_id != user_id:
                        issue = f"Redis: Memory {memory.id} in {user_id}'s data belongs to {memory_user_id}"
                        results["issues"].append(issue)
                        results["passed"] = False

                    # Check for other users' identifiers in content
                    for other_user in self.test_users:
                        if other_user != user_id and other_user in memory.content:
                            contamination = f"Redis: User {user_id} can see {other_user}'s data in memory {memory.id}"
                            results["cross_contamination"].append(contamination)
                            results["passed"] = False

                # Verify user can only access their own memories
                expected_count = len(self.test_memories[user_id])
                actual_count = len(user_memories)

                if actual_count != expected_count:
                    issue = f"Redis: User {user_id} expected {expected_count} memories, got {actual_count}"
                    results["issues"].append(issue)
                    results["passed"] = False

            # Test cross-user access attempts
            await self._test_redis_cross_access(results)

        except Exception as e:
            results["issues"].append(f"Redis isolation test failed: {str(e)}")
            results["passed"] = False
            logger.error(f"Redis isolation test error: {e}")

        return results

    async def _test_redis_cross_access(self, results: Dict[str, Any]):
        """Test if users can access other users' Redis data."""
        logger.info("Testing Redis cross-user access prevention...")

        try:
            user_a, user_b = self.test_users[0], self.test_users[1]

            # Try to get user B's memory using user A's context
            user_b_memories = self.test_memories[user_b]
            if user_b_memories:
                memory_id = user_b_memories[0].id

                # This should return None (no access)
                cross_access_memory = await self.redis_store.get_memory(
                    user_a, memory_id
                )

                if cross_access_memory is not None:
                    issue = f"Redis: User {user_a} can access user {user_b}'s memory {memory_id}"
                    results["issues"].append(issue)
                    results["passed"] = False

        except Exception as e:
            results["issues"].append(f"Redis cross-access test failed: {str(e)}")
            results["passed"] = False
            logger.error(f"Redis cross-access test error: {e}")

    async def test_vector_isolation(self) -> Dict[str, Any]:
        """Test Vector store data isolation between users."""
        logger.info("Testing Vector store data isolation...")

        results = {
            "test_name": "Vector Store Data Isolation",
            "passed": True,
            "issues": [],
            "user_data_counts": {},
            "cross_contamination": [],
            "search_isolation": [],
        }

        try:
            for user_id in self.test_users:
                # Get all memories for this user
                user_memories = await self.vector_store.get_user_memories(user_id)
                results["user_data_counts"][user_id] = len(user_memories)

                # Verify all memories belong to this user
                for memory in user_memories:
                    memory_user = memory["metadata"].get("user_id")
                    if memory_user != user_id:
                        issue = f"Vector: Memory {memory['memory_id']} in {user_id}'s data belongs to {memory_user}"
                        results["issues"].append(issue)
                        results["passed"] = False

                # Test similarity search isolation
                await self._test_vector_search_isolation(user_id, results)

        except Exception as e:
            results["issues"].append(f"Vector isolation test failed: {str(e)}")
            results["passed"] = False
            logger.error(f"Vector isolation test error: {e}")

        return results

    async def _test_vector_search_isolation(
        self, user_id: str, results: Dict[str, Any]
    ):
        """Test that similarity search only returns user's own data."""
        logger.info(f"Testing vector search isolation for user {user_id}...")

        try:
            # Search for terms that should exist in other users' data
            for other_user in self.test_users:
                if other_user != user_id:
                    # Search for the other user's unique identifier
                    search_query = f"secret information {other_user}"
                    search_results = await self.vector_store.similarity_search(
                        search_query, user_id, k=10
                    )

                    # Check if any results contain other users' data
                    for result in search_results:
                        result_user = result["metadata"].get("user_id")
                        if result_user != user_id:
                            contamination = f"Vector search: User {user_id} found {result_user}'s data: {result['memory_id']}"
                            results["cross_contamination"].append(contamination)
                            results["passed"] = False

                        # Check content for other users' identifiers
                        if other_user in result["content"]:
                            contamination = f"Vector search: User {user_id} can see {other_user}'s identifiers in search results"
                            results["search_isolation"].append(contamination)
                            results["passed"] = False

        except Exception as e:
            results["search_isolation"].append(
                f"Vector search isolation test failed: {str(e)}"
            )
            results["passed"] = False
            logger.error(f"Vector search isolation test error: {e}")

    async def test_data_leakage_scenarios(self) -> Dict[str, Any]:
        """Test various data leakage scenarios."""
        logger.info("Testing data leakage scenarios...")

        results = {
            "test_name": "Data Leakage Prevention",
            "passed": True,
            "scenarios_tested": [],
            "vulnerabilities": [],
        }

        try:
            # Scenario 1: Empty user ID
            try:
                empty_memories = await self.redis_store.get_user_memories("")
                if empty_memories:
                    results["vulnerabilities"].append(
                        "Redis: Empty user_id returns data"
                    )
                    results["passed"] = False
            except Exception:
                pass  # Expected to fail
            results["scenarios_tested"].append("Empty user ID")

            # Scenario 2: SQL injection-like attempts
            malicious_user_id = "'; DROP TABLE users; --"
            try:
                malicious_memories = await self.redis_store.get_user_memories(
                    malicious_user_id
                )
                # Should return empty list, not error
                if len(malicious_memories) > 0:
                    results["vulnerabilities"].append(
                        "Redis: Malicious user_id returns unexpected data"
                    )
                    results["passed"] = False
            except Exception:
                pass  # Errors are acceptable for malicious input
            results["scenarios_tested"].append("Malicious user ID")

            # Scenario 3: User ID manipulation
            if self.test_users:
                user_a = self.test_users[0]
                manipulated_id = user_a + "_modified"
                manipulated_memories = await self.redis_store.get_user_memories(
                    manipulated_id
                )
                if len(manipulated_memories) > 0:
                    results["vulnerabilities"].append(
                        "Redis: Modified user_id returns data"
                    )
                    results["passed"] = False
                results["scenarios_tested"].append("Modified user ID")

            # Scenario 4: Cross-user search in vector store
            if len(self.test_users) >= 2 and all(
                self.test_memories.get(user) for user in self.test_users[:2]
            ):
                user_a, user_b = self.test_users[0], self.test_users[1]
                user_b_content = self.test_memories[user_b][0].content[:50]

                # User A searches for User B's exact content
                cross_search = await self.vector_store.similarity_search(
                    user_b_content, user_a, k=5
                )
                for result in cross_search:
                    if result["metadata"].get("user_id") != user_a:
                        results["vulnerabilities"].append(
                            f"Vector: Cross-user content search found other user's data"
                        )
                        results["passed"] = False
                        break
                results["scenarios_tested"].append("Cross-user content search")

        except Exception as e:
            results["vulnerabilities"].append(f"Data leakage test failed: {str(e)}")
            results["passed"] = False
            logger.error(f"Data leakage test error: {e}")

        return results

    async def test_key_namespace_isolation(self) -> Dict[str, Any]:
        """Test Redis key namespace isolation."""
        logger.info("Testing Redis key namespace isolation...")

        results = {
            "test_name": "Redis Key Namespace Isolation",
            "passed": True,
            "key_patterns": {},
            "namespace_violations": [],
        }

        try:
            # Get Redis client for direct key inspection
            await self.redis_store._ensure_initialized()
            if not self.redis_store.client:
                results["issues"] = ["Could not access Redis client for key inspection"]
                results["passed"] = False
                return results

            # Check key patterns for each user
            for user_id in self.test_users:
                user_pattern = f"user:{user_id}:*"
                user_keys = await self.redis_store.client.keys(user_pattern)
                results["key_patterns"][user_id] = len(user_keys)

                # Verify all keys contain the user ID
                for key in user_keys:
                    if isinstance(key, bytes):
                        key = key.decode()
                    if f"user:{user_id}:" not in key:
                        violation = f"Key {key} doesn't follow user namespace pattern"
                        results["namespace_violations"].append(violation)
                        results["passed"] = False

        except Exception as e:
            results["namespace_violations"].append(
                f"Key namespace test failed: {str(e)}"
            )
            results["passed"] = False
            logger.error(f"Key namespace test error: {e}")

        return results

    async def test_vector_namespace_isolation(self) -> Dict[str, Any]:
        """Test vector store namespace isolation."""
        logger.info("Testing vector store namespace isolation...")

        results = {
            "test_name": "Vector Store Namespace Isolation",
            "passed": True,
            "namespaces": {},
            "isolation_verified": True,
        }

        try:
            # Check if using Pinecone namespaces or ChromaDB metadata filtering
            if self.vector_store.use_pinecone:
                # Test Pinecone namespace isolation
                for user_id in self.test_users:
                    namespace = self.vector_store._get_user_namespace(user_id)
                    results["namespaces"][user_id] = namespace

                    # Each user should have their own namespace
                    if not namespace.startswith(f"user_{user_id}"):
                        results["passed"] = False
                        results["isolation_verified"] = False
            else:
                # Test ChromaDB metadata filtering
                for user_id in self.test_users:
                    metadata_filter = self.vector_store._get_user_metadata_filter(
                        user_id
                    )
                    if metadata_filter.get("user_id") != user_id:
                        results["passed"] = False
                        results["isolation_verified"] = False

        except Exception as e:
            results["isolation_verified"] = False
            results["passed"] = False
            logger.error(f"Vector namespace test error: {e}")

        return results

    async def cleanup(self):
        """Clean up test data."""
        logger.info("Cleaning up test data...")

        try:
            for user_id in self.test_users:
                # Clear Redis data
                try:
                    await self.redis_store.clear_user_memories(user_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to clear Redis data for user {user_id}: {e}"
                    )

                # Clear vector data
                try:
                    await self.vector_store.clear_user_memories(user_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to clear vector data for user {user_id}: {e}"
                    )

            logger.info("Test cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all privacy and isolation tests."""
        logger.info("Starting comprehensive privacy retrieval tests...")

        test_results = {
            "test_suite": "Privacy and Data Isolation Test Suite",
            "timestamp": datetime.now().isoformat(),
            "overall_passed": True,
            "tests": [],
        }

        try:
            await self.setup()

            # Run all test categories
            tests = [
                self.test_redis_isolation(),
                self.test_vector_isolation(),
                self.test_data_leakage_scenarios(),
                self.test_key_namespace_isolation(),
                self.test_vector_namespace_isolation(),
            ]

            for test_coro in tests:
                try:
                    result = await test_coro
                    test_results["tests"].append(result)

                    if not result["passed"]:
                        test_results["overall_passed"] = False

                except Exception as e:
                    logger.error(f"Test failed with exception: {e}")
                    test_results["tests"].append(
                        {"test_name": "Failed Test", "passed": False, "error": str(e)}
                    )
                    test_results["overall_passed"] = False

        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            test_results["overall_passed"] = False
            test_results["error"] = str(e)

        finally:
            await self.cleanup()

        return test_results


async def main():
    """Run the privacy retrieval test suite."""
    test_suite = PrivacyRetrievalTest()
    results = await test_suite.run_all_tests()

    # Print results
    print("\n" + "=" * 60)
    print("PRIVACY AND DATA ISOLATION TEST RESULTS")
    print("=" * 60)

    print(
        f"Overall Status: {'✅ PASSED' if results['overall_passed'] else '❌ FAILED'}"
    )
    print(f"Test Timestamp: {results['timestamp']}")
    print()

    for test in results["tests"]:
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        print(f"{status} - {test['test_name']}")

        if "issues" in test and test["issues"]:
            print("   Issues found:")
            for issue in test["issues"]:
                print(f"     - {issue}")

        if "vulnerabilities" in test and test["vulnerabilities"]:
            print("   Security vulnerabilities:")
            for vuln in test["vulnerabilities"]:
                print(f"     - {vuln}")

        if "cross_contamination" in test and test["cross_contamination"]:
            print("   Cross-user data contamination:")
            for contam in test["cross_contamination"]:
                print(f"     - {contam}")

        print()

    # Summary
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"] if test["passed"])

    print(f"Summary: {passed_tests}/{total_tests} tests passed")

    if not results["overall_passed"]:
        print("\n⚠️  CRITICAL: Privacy violations detected!")
        print("   These issues must be resolved before production deployment.")
        return 1
    else:
        print("\n✅ All privacy and isolation tests passed!")
        print("   User data is properly isolated in both storage systems.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
