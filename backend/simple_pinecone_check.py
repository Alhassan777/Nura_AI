#!/usr/bin/env python3
"""
Simple Pinecone Connection Test
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

    print("🔍 Testing basic Pinecone connection...")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)

    # Try to list indexes (this should work even if no indexes exist)
    print("\n📋 Attempting to list indexes...")
    indexes = pc.list_indexes()

    print("✅ Successfully connected to Pinecone!")
    print(f"Found {len(indexes)} indexes in your account")

    if indexes:
        for index in indexes:
            print(f"  - Index: {index.name}")
            print(f"    Host: {index.host}")
            print(f"    Status: {index.status}")
    else:
        print("No indexes found - this is normal for a new account")

    print("\n🎯 Your Pinecone connection is working!")
    print("The issue might be with the ServerlessSpec configuration.")
    print("\nNext steps:")
    print("1. Go to https://app.pinecone.io/")
    print("2. Create an index manually with these settings:")
    print("   - Name: nura")
    print("   - Dimensions: 768")
    print("   - Metric: cosine")
    print("   - Cloud: Choose your preferred cloud (AWS/GCP)")
    print("3. Note the environment/region from the console")
    print("4. Update PINECONE_ENVIRONMENT in .env.local")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Verify your API key at https://app.pinecone.io/")
    print("2. Check if your account is active")
    print("3. Ensure you have internet connectivity")
