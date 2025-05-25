#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

print("=== Environment Variables ===")
print(f"VECTOR_DB_TYPE: {os.getenv('VECTOR_DB_TYPE')}")
print(f"PINECONE_API_KEY: {'SET' if os.getenv('PINECONE_API_KEY') else 'NOT SET'}")
print(f"GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
print(
    f"GOOGLE_CLOUD_PROJECT: {'SET' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'NOT SET'}"
)

print("\n=== Testing Config Import ===")
try:
    from services.memory.config import Config

    print("✅ Config imported successfully")

    print(f"Config.VECTOR_DB_TYPE: {Config.VECTOR_DB_TYPE}")
    print(f"Config.PINECONE_API_KEY: {'SET' if Config.PINECONE_API_KEY else 'NOT SET'}")
    print(f"Config.GOOGLE_API_KEY: {'SET' if Config.GOOGLE_API_KEY else 'NOT SET'}")

    print("\n=== Testing Config Validation ===")
    Config.validate()
    print("✅ Config validation passed")

except Exception as e:
    print(f"❌ Config error: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Testing Memory Service Import ===")
try:
    from services.memory.memoryService import MemoryService

    print("✅ MemoryService imported successfully")

    print("\n=== Testing Memory Service Initialization ===")
    memory_service = MemoryService()
    print("✅ MemoryService initialized successfully")

except Exception as e:
    print(f"❌ MemoryService error: {e}")
    import traceback

    traceback.print_exc()
