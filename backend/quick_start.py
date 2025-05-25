#!/usr/bin/env python3
"""
Nura Memory System Quick Start Script

This script helps you get the memory system up and running quickly.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path


def print_banner():
    """Print welcome banner."""
    print("🧠" + "=" * 58 + "🧠")
    print("🚀 NURA MEMORY SYSTEM - QUICK START 🚀")
    print("🧠" + "=" * 58 + "🧠")
    print()


def check_requirements():
    """Check if all requirements are installed."""
    print("📋 Checking Requirements...")
    print("-" * 30)

    missing = []

    # Check Python packages
    required_packages = [
        "fastapi",
        "uvicorn",
        "redis",
        "chromadb",
        "google.generativeai",
        "presidio_analyzer",
        "transformers",
    ]

    for package in required_packages:
        try:
            __import__(package.replace("-", "_").replace(".", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)

    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("💡 Run: pip install -r requirements.txt")
        return False

    print("✅ All Python packages are installed!")
    return True


def check_redis():
    """Check if Redis is running."""
    print("\n🔴 Checking Redis...")
    print("-" * 20)

    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is running!")
        return True
    except Exception as e:
        print("❌ Redis is not running!")
        print("💡 Start Redis with: redis-server")
        print(
            "💡 Or install Redis: brew install redis (macOS) / apt-get install redis-server (Ubuntu)"
        )
        return False


def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\n🔧 Checking Environment Configuration...")
    print("-" * 40)

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("💡 Copy env_template.txt to .env and fill in your values")
        print("💡 Most importantly, set your GOOGLE_API_KEY")
        return False

    # Load .env file
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print("❌ python-dotenv not installed!")
        return False

    # Check required variables
    required_vars = ["GOOGLE_API_KEY", "REDIS_URL"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value == "your_gemini_api_key_here":
            missing_vars.append(var)
            print(f"❌ {var} not set")
        else:
            print(f"✅ {var} configured")

    if missing_vars:
        print(
            f"\n⚠️ Please set these variables in your .env file: {', '.join(missing_vars)}"
        )
        return False

    return True


def create_data_directory():
    """Create data directory for vector storage."""
    print("\n📁 Setting up Data Directory...")
    print("-" * 30)

    data_dir = Path("./data/vector_store")
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created data directory: {data_dir}")


async def test_system():
    """Test the memory system."""
    print("\n🧪 Testing Memory System...")
    print("-" * 25)

    try:
        # Quick test of vector database
        sys.path.append("src")
        from services.memory.storage.vector_store import VectorStore

        vector_store = VectorStore(
            persist_directory="./data/vector_store",
            project_id="local",
            use_vertex=False,
        )

        # Test embedding generation
        test_embedding = await vector_store._get_embedding("test message")
        print(f"✅ Vector database working! (embedding size: {len(test_embedding)})")

        return True

    except Exception as e:
        print(f"❌ System test failed: {str(e)}")
        return False


def launch_chat_interface():
    """Launch the chat interface."""
    print("\n🚀 Launching Chat Interface...")
    print("-" * 30)
    print("🌐 Opening browser to: http://localhost:8000")
    print("🧪 Try these test scenarios:")
    print("   • Crisis: 'I want to end it all'")
    print("   • PII: 'My name is Sarah, I take Zoloft'")
    print("   • Anchors: 'Mad World song speaks to me'")
    print("   • Context: Send multiple related messages")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    # Launch the chat interface
    try:
        subprocess.run([sys.executable, "chat_test_interface.py"])
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped. Thanks for testing!")


async def main():
    """Main setup and launch function."""
    print_banner()

    # Step 1: Check requirements
    if not check_requirements():
        print("\n❌ Please install missing requirements first.")
        return

    # Step 2: Check Redis
    if not check_redis():
        print("\n❌ Please start Redis first.")
        return

    # Step 3: Check environment
    if not check_env_file():
        print("\n❌ Please configure your .env file first.")
        return

    # Step 4: Create data directory
    create_data_directory()

    # Step 5: Test system
    if not await test_system():
        print("\n❌ System test failed. Check your configuration.")
        return

    print("\n🎉 ALL CHECKS PASSED!")
    print("✅ Requirements installed")
    print("✅ Redis running")
    print("✅ Environment configured")
    print("✅ Vector database working")
    print("✅ Memory system ready")

    # Step 6: Launch chat interface
    input("\nPress Enter to launch the chat interface...")
    launch_chat_interface()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled. Run again when ready!")
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("💡 Check the error message above and try again.")
