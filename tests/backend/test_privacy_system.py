#!/usr/bin/env python3
"""
Test script for the 3-option privacy system
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = f"test-privacy-user-{int(time.time())}"


def test_privacy_system():
    print(f"🧪 Testing Privacy System for user: {USER_ID}")
    print("=" * 60)

    # Step 1: Create some memories with PII
    print("\n1️⃣ Creating memories with PII...")

    test_messages = [
        "My name is John Smith and I live in New York",
        "I feel happy because I met my girlfriend Sarah for the first time in Paris",
        "My phone number is 555-123-4567 and I work at Google",
        "Egypt represents my home country where I feel the warmth of family love",
    ]

    for i, message in enumerate(test_messages):
        print(f"   📝 Storing: {message}")
        response = requests.post(
            f"{BASE_URL}/memory/dual-storage",
            params={"user_id": USER_ID},
            json={"content": message, "type": "chat"},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Stored {result.get('stored_components', 0)} components")
        else:
            print(f"   ❌ Error: {response.status_code}")

    # Step 2: Get privacy review
    print("\n2️⃣ Getting privacy review...")

    response = requests.get(f"{BASE_URL}/memory/privacy-review/{USER_ID}")

    if response.status_code == 200:
        privacy_data = response.json()
        memories_with_pii = privacy_data.get("memories_with_pii", [])

        print(f"   📊 Found {len(memories_with_pii)} memories with PII")

        for memory in memories_with_pii:
            print(f"   🔍 Memory: {memory['content'][:50]}...")
            print(f"      📍 Storage: {memory['storage_type']}")
            print(f"      🚨 PII Types: {memory['pii_summary']['types']}")
            print(
                f"      ⚠️  Risk Levels: H:{memory['pii_summary']['high_risk_count']} M:{memory['pii_summary']['medium_risk_count']} L:{memory['pii_summary']['low_risk_count']}"
            )
            print()

        # Step 3: Test the 3 privacy options
        print("3️⃣ Testing privacy options...")

        if memories_with_pii:
            # Create test choices for each option
            choices = {}

            for i, memory in enumerate(memories_with_pii[:3]):  # Test first 3 memories
                if i == 0:
                    choices[memory["id"]] = "remove_entirely"
                    print(f"   🗑️  Memory 1: Remove entirely")
                elif i == 1:
                    choices[memory["id"]] = "remove_pii_only"
                    print(f"   🔒 Memory 2: Remove PII only")
                elif i == 2:
                    choices[memory["id"]] = "keep_original"
                    print(f"   ✅ Memory 3: Keep original")

            # Apply choices
            print("\n   📤 Applying privacy choices...")
            response = requests.post(
                f"{BASE_URL}/memory/apply-privacy-choices/{USER_ID}", json=choices
            )

            if response.status_code == 200:
                results = response.json()
                summary = results.get("summary", {})

                print(f"   ✅ Privacy choices applied successfully!")
                print(
                    f"      🗑️  Removed entirely: {summary.get('removed_entirely', 0)}"
                )
                print(f"      🔒 PII removed: {summary.get('pii_removed', 0)}")
                print(f"      ✅ Kept original: {summary.get('kept_original', 0)}")
                print(f"      📊 Total processed: {summary.get('total_processed', 0)}")

                # Show details of processed memories
                for processed in results.get("processed", []):
                    action = processed.get("action")
                    if action == "removed_entirely":
                        print(
                            f"      🗑️  Deleted: {processed.get('original_content', '')[:30]}..."
                        )
                    elif action == "pii_removed":
                        print(
                            f"      🔒 Anonymized: {processed.get('original_content', '')[:30]}..."
                        )
                        print(
                            f"         ➡️  Became: {processed.get('anonymized_content', '')[:30]}..."
                        )
                    elif action == "kept_original":
                        print(f"      ✅ Kept: {processed.get('content', '')[:30]}...")

            else:
                print(f"   ❌ Error applying choices: {response.status_code}")
                print(f"      {response.text}")

        # Step 4: Verify changes
        print("\n4️⃣ Verifying changes...")

        response = requests.get(f"{BASE_URL}/memory/privacy-review/{USER_ID}")
        if response.status_code == 200:
            updated_privacy_data = response.json()
            updated_memories = updated_privacy_data.get("memories_with_pii", [])

            print(f"   📊 Memories with PII after changes: {len(updated_memories)}")

            for memory in updated_memories:
                privacy_choice = memory.get("metadata", {}).get(
                    "privacy_choice", "unknown"
                )
                print(f"   📝 {memory['content'][:40]}... (Choice: {privacy_choice})")

    else:
        print(f"   ❌ Error getting privacy review: {response.status_code}")

    print("\n" + "=" * 60)
    print("🎉 Privacy system test completed!")


if __name__ == "__main__":
    test_privacy_system()
