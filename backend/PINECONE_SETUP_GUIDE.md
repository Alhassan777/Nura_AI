# Pinecone Vector Database Setup Guide

## 🎯 Quick Setup: Migrating from Google Cloud to Pinecone

This guide will help you migrate your Nura memory system from Google Cloud Vertex AI to Pinecone vector database.

## 📋 Why Pinecone?

- ✅ **Managed Service**: No infrastructure to manage
- ✅ **High Performance**: Optimized for vector similarity search
- ✅ **Scalable**: Handles millions of vectors easily
- ✅ **Cost Effective**: Pay only for what you use
- ✅ **Easy Setup**: Get started in minutes

## 🚀 Step 1: Create Pinecone Account

1. **Sign up at [Pinecone.io](https://www.pinecone.io/)**
2. **Choose a plan:**

   - **Starter (Free)**: 1 index, 100K vectors, perfect for testing
   - **Standard**: Multiple indexes, more vectors for production

3. **Get your API credentials:**
   - Go to [Pinecone Console](https://app.pinecone.io/)
   - Navigate to "API Keys" section
   - Copy your **API Key**
   - Note your **Environment** (e.g., `us-east-1-aws`, `gcp-starter`)

## 🔧 Step 2: Update Your Configuration

### Update `.env.local` file:

```bash
# === VECTOR DATABASE CONFIGURATION ===
# Set Pinecone as your vector database
VECTOR_DB_TYPE=pinecone

# Pinecone Configuration
PINECONE_API_KEY=your_actual_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=nura-memories

# Keep your Google API key for embeddings
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Example with real values:

```bash
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=pcsk_1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=nura-memories
GOOGLE_API_KEY=AIzaSyC1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

## 📦 Step 3: Install Dependencies

```bash
# Install Pinecone client
pip install pinecone-client==3.0.0

# Or if using the requirements.txt (already updated)
pip install -r requirements.txt
```

## 🧪 Step 4: Test Your Configuration

Create a test script to verify Pinecone connection:

```python
# test_pinecone_setup.py
import os
import asyncio
from src.services.memory.storage.vector_store import VectorStore
from src.services.memory.types import MemoryItem
from datetime import datetime
import uuid

async def test_pinecone_setup():
    """Test Pinecone vector database setup."""
    print("🧪 Testing Pinecone Vector Database Setup...")
    print("=" * 50)

    try:
        # Initialize vector store with Pinecone
        print("1️⃣ Initializing Pinecone vector store...")
        vector_store = VectorStore(
            vector_db_type="pinecone"
        )
        print("✅ Pinecone vector store initialized successfully!")

        # Create test memory
        print("\n2️⃣ Creating test memory...")
        test_memory = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user_pinecone",
            content="I feel anxious about my upcoming presentation at work",
            type="test",
            timestamp=datetime.utcnow(),
            metadata={"test": True, "emotion": "anxiety"}
        )

        # Add memory to Pinecone
        print("3️⃣ Adding memory to Pinecone...")
        await vector_store.add_memory("test_user_pinecone", test_memory)
        print("✅ Successfully added test memory to Pinecone!")

        # Test similarity search
        print("\n4️⃣ Testing similarity search...")
        similar_memories = await vector_store.get_similar_memories(
            "test_user_pinecone",
            "work stress and anxiety",
            limit=1
        )
        print(f"✅ Found {len(similar_memories)} similar memories!")

        if similar_memories:
            memory = similar_memories[0]
            print(f"   📝 Content: {memory.content}")
            print(f"   🏷️  Type: {memory.type}")

        # Test memory count
        print("\n5️⃣ Testing memory count...")
        count = await vector_store.get_memory_count("test_user_pinecone")
        print(f"✅ User has {count} memories in Pinecone")

        # Clean up test data
        print("\n6️⃣ Cleaning up test data...")
        await vector_store.clear_memories("test_user_pinecone")
        print("✅ Test data cleaned up")

        print("\n🎉 Pinecone setup test completed successfully!")
        print("Your vector database is ready for production use.")

    except Exception as e:
        print(f"\n❌ Error during Pinecone setup test: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your PINECONE_API_KEY is correct")
        print("2. Verify your PINECONE_ENVIRONMENT matches your account")
        print("3. Ensure you have internet connectivity")
        print("4. Check Pinecone service status at https://status.pinecone.io/")

if __name__ == "__main__":
    asyncio.run(test_pinecone_setup())
```

Run the test:

```bash
python test_pinecone_setup.py
```

## 🔄 Step 5: Migrate Existing Data (Optional)

If you have existing data in Google Cloud Vertex AI or ChromaDB, you can migrate it:

```python
# migrate_to_pinecone.py
import asyncio
from src.services.memory.storage.vector_store import VectorStore

async def migrate_data():
    """Migrate data from old vector database to Pinecone."""
    print("🔄 Migrating data to Pinecone...")

    # Initialize old vector store (ChromaDB)
    old_store = VectorStore(
        persist_directory="./data/vector_store",
        vector_db_type="chroma"
    )

    # Initialize new vector store (Pinecone)
    new_store = VectorStore(
        vector_db_type="pinecone"
    )

    # Get all users (you'll need to implement this based on your data)
    users = ["user1", "user2"]  # Replace with actual user IDs

    for user_id in users:
        print(f"Migrating data for user: {user_id}")

        # Get all memories from old store
        # Note: You might need to implement a get_all_memories method
        # or query with a broad search term
        memories = await old_store.get_similar_memories(
            user_id, "", limit=1000  # Get many memories
        )

        # Add each memory to new store
        for memory in memories:
            await new_store.add_memory(user_id, memory)
            print(f"  ✅ Migrated memory: {memory.id}")

    print("🎉 Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
```

## 🚀 Step 6: Start Your Services

1. **Start Redis** (for short-term memory):

```bash
redis-server
```

2. **Start the Memory Service**:

```bash
python -m src.services.memory.main
```

3. **Start your Next.js app**:

```bash
npm run dev
```

## 📊 Step 7: Verify Everything Works

1. **Open your chat interface**: http://localhost:3000/test-chat
2. **Send a test message**: "I'm feeling stressed about work"
3. **Send a follow-up**: "What can help with work stress?"
4. **Check if the system uses context** from the first message

## 🔍 Monitoring Your Pinecone Usage

1. **Go to [Pinecone Console](https://app.pinecone.io/)**
2. **Check your index**: `nura-memories`
3. **Monitor**:
   - Vector count
   - Query usage
   - Storage usage
   - Costs

## 🚨 Troubleshooting

### Error: "Pinecone not available"

```bash
pip install pinecone-client==3.0.0
```

### Error: "Invalid API key"

- Check your API key in Pinecone console
- Ensure no extra spaces in `.env.local`
- Restart your services after updating environment

### Error: "Environment not found"

- Verify your environment name (e.g., `us-east-1-aws`)
- Check Pinecone console for correct environment

### Error: "Index not found"

- The system will auto-create the index
- If issues persist, create manually in Pinecone console:
  - Name: `nura-memories`
  - Dimensions: `768`
  - Metric: `cosine`

### Performance Issues

- Check your Pinecone plan limits
- Monitor query rate limits
- Consider upgrading plan for production

## 💰 Cost Optimization

### Free Tier Limits:

- 1 index
- 100K vectors
- Perfect for testing and small deployments

### Production Tips:

- Monitor vector count in Pinecone console
- Implement memory cleanup for old/irrelevant memories
- Use memory scoring to store only valuable memories

## 🔒 Security Best Practices

1. **Keep API keys secure**:

   - Never commit API keys to git
   - Use environment variables
   - Rotate keys regularly

2. **User data isolation**:

   - All queries include user_id filters
   - Memories are isolated per user
   - No cross-user data leakage

3. **Data privacy**:
   - PII detection still works with Pinecone
   - Sensitive data is anonymized before storage
   - Audit logging tracks all operations

## 🎯 Performance Comparison

| Feature     | ChromaDB (Local)        | Google Vertex AI     | Pinecone               |
| ----------- | ----------------------- | -------------------- | ---------------------- |
| Setup       | ✅ Zero setup           | ⚠️ Complex GCP setup | ✅ 5-minute setup      |
| Cost        | ✅ Free                 | 💰 Pay per query     | 💰 Predictable pricing |
| Speed       | ✅ Very fast (local)    | ⚠️ Network latency   | ✅ Optimized for speed |
| Scale       | ⚠️ Single machine       | ✅ Unlimited         | ✅ Millions of vectors |
| Maintenance | ⚠️ Manual backups       | ✅ Fully managed     | ✅ Fully managed       |
| Reliability | ⚠️ Single point failure | ✅ Enterprise grade  | ✅ 99.9% uptime        |

## ✅ Migration Checklist

- [ ] Created Pinecone account
- [ ] Got API key and environment
- [ ] Updated `.env.local` with Pinecone credentials
- [ ] Set `VECTOR_DB_TYPE=pinecone`
- [ ] Installed `pinecone-client==3.0.0`
- [ ] Ran test script successfully
- [ ] Started all services (Redis, Memory Service, Next.js)
- [ ] Tested chat interface with memory context
- [ ] Verified memories are stored in Pinecone console
- [ ] (Optional) Migrated existing data
- [ ] Set up monitoring in Pinecone console

## 🎉 You're Done!

Your Nura memory system is now powered by Pinecone! You get:

- **Managed vector database** - no infrastructure to maintain
- **High performance** - optimized for similarity search
- **Scalability** - handles growth automatically
- **Reliability** - enterprise-grade uptime
- **Cost predictability** - clear pricing model

Your mental health assistant now has a robust, scalable memory system that can grow with your users! 🧠✨
