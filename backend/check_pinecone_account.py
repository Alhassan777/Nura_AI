#!/usr/bin/env python3
"""
Check Pinecone Account Configuration

This script helps you find the correct environment for your Pinecone account.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

try:
    from pinecone import Pinecone

    # Get API key
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        print("❌ PINECONE_API_KEY not found in .env.local")
        exit(1)

    print("🔍 Checking your Pinecone account...")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)

    # List available indexes
    print("\n📋 Available indexes in your account:")
    indexes = pc.list_indexes()

    if not indexes:
        print("   No indexes found in your account")
        print("\n💡 Suggested next steps:")
        print("   1. Create an index in Pinecone console")
        print("   2. Or let the system auto-create one")

        # Try to create an index to see what environments are available
        print("\n🌍 Attempting to find available environments...")

        # Common Pinecone environments to try
        environments_to_try = [
            "gcp-starter",
            "us-east-1-aws",
            "us-west-2-aws",
            "eu-west-1-aws",
            "asia-southeast-1-aws",
            "us-central1-gcp",
            "europe-west1-gcp",
            "asia-northeast1-gcp",
        ]

        for env in environments_to_try:
            try:
                print(f"   Trying environment: {env}")
                from pinecone import ServerlessSpec

                pc.create_index(
                    name="test-env-check",
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws" if "aws" in env else "gcp", region=env
                    ),
                )
                print(f"   ✅ SUCCESS! Environment '{env}' works for your account")

                # Delete the test index
                pc.delete_index("test-env-check")
                print(f"   🗑️ Cleaned up test index")

                print(f"\n🎯 Update your .env.local with:")
                print(f"PINECONE_ENVIRONMENT={env}")
                break

            except Exception as e:
                if "already exists" in str(e):
                    print(
                        f"   ✅ Environment '{env}' works (test index already exists)"
                    )
                    print(f"\n🎯 Update your .env.local with:")
                    print(f"PINECONE_ENVIRONMENT={env}")
                    break
                else:
                    print(f"   ❌ Environment '{env}' not available: {str(e)[:100]}...")
                    continue
        else:
            print("\n❌ Could not find a working environment")
            print("Please check your Pinecone console for the correct environment")
    else:
        print(f"   Found {len(indexes)} indexes:")
        for index in indexes:
            print(f"   - {index.name}")
            print(f"     Host: {index.host}")
            print(f"     Dimension: {index.dimension}")
            print(f"     Metric: {index.metric}")

            # Extract environment from host
            if index.host:
                host_parts = index.host.split(".")
                if len(host_parts) > 1:
                    env = host_parts[1]
                    print(f"     Environment: {env}")
                    print(f"\n🎯 Update your .env.local with:")
                    print(f"PINECONE_ENVIRONMENT={env}")
                    print(f"PINECONE_INDEX_NAME={index.name}")
            print()

except ImportError:
    print("❌ Pinecone client not installed")
    print("Run: pip install pinecone-client==3.0.0")
except Exception as e:
    print(f"❌ Error checking Pinecone account: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check your PINECONE_API_KEY is correct")
    print("2. Ensure you have internet connectivity")
    print("3. Visit https://app.pinecone.io/ to verify your account")
