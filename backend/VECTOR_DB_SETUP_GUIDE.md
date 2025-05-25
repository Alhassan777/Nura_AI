# Vector Database Setup Guide for Nura Memory System

## 🎯 Quick Answer: What You Need to Do

**Good News:** ChromaDB requires **NO registration or external setup!** It's a local, embedded database that works out of the box.

## 📋 Vector Database Options

### Option 1: ChromaDB (Recommended - No Setup Required)

- ✅ **No registration needed**
- ✅ **No external services**
- ✅ **Works locally**
- ✅ **Already configured in your system**

### Option 2: Google Vertex AI (Advanced - Requires Google Cloud)

- ⚠️ Requires Google Cloud account
- ⚠️ Requires billing setup
- ⚠️ More complex configuration

## 🚀 ChromaDB Setup (Default - Already Working!)

### 1. Verify ChromaDB is Working

```bash
# Test ChromaDB installation
python -c "import chromadb; print('ChromaDB is installed and ready!')"
```

### 2. Check Your Current Configuration

Your system is already configured to use ChromaDB by default. Check your current setup:

```python
# test_vector_db.py
import asyncio
from src.services.memory.storage.vector_store import VectorStore

async def test_vector_db():
    # This creates a local ChromaDB instance
    vector_store = VectorStore(
        persist_directory="./data/vector_store",
        project_id="local",  # Not used for ChromaDB
        use_vertex=False     # Use ChromaDB, not Vertex AI
    )

    print("✅ Vector database initialized successfully!")
    print(f"📁 Data will be stored in: ./data/vector_store")

    # Test basic functionality
    from src.services.memory.types import MemoryItem
    from datetime import datetime
    import uuid

    test_memory = MemoryItem(
        id=str(uuid.uuid4()),
        userId="test_user",
        content="This is a test memory for vector storage",
        type="test",
        timestamp=datetime.utcnow(),
        metadata={"test": True}
    )

    try:
        await vector_store.add_memory("test_user", test_memory)
        print("✅ Successfully added test memory to vector database!")

        # Test retrieval
        similar = await vector_store.get_similar_memories(
            "test_user",
            "test memory",
            limit=1
        )
        print(f"✅ Successfully retrieved {len(similar)} similar memories!")

    except Exception as e:
        print(f"❌ Error testing vector database: {e}")

if __name__ == "__main__":
    asyncio.run(test_vector_db())
```

### 3. Run the Test

```bash
python test_vector_db.py
```

## 📁 Data Storage Location

Your vector database data is stored locally at:

```
./data/vector_store/
```

This directory will be created automatically when you first use the system.

## 🔧 Environment Configuration

Your `.env` file should have:

```bash
# Vector Database Configuration
MEMORY_VECTOR_STORE_PATH=./data/vector_store
GOOGLE_API_KEY=your_gemini_api_key_here  # For embeddings

# Optional: Use Vertex AI instead of ChromaDB
# GOOGLE_CLOUD_PROJECT=your_project_id
# GOOGLE_CLOUD_LOCATION=us-central1
# USE_VERTEX_AI=false  # Set to true for Vertex AI
```

## 🧪 Testing Vector Database with Chat Interface

1. **Start the chat interface:**

```bash
python chat_test_interface.py
```

2. **Open browser to:** http://localhost:8000

3. **Test vector storage by:**
   - Sending a message: "I love listening to jazz music when I'm stressed"
   - Sending another: "What music helps with anxiety?"
   - The system should use the first message as context for the second!

## 🔍 How Vector Database Works in Your System

```
User Message → Embedding Generation → Vector Storage → Similarity Search
     ↓              ↓                      ↓              ↓
"I feel sad"   [0.1, 0.8, ...]     ChromaDB Store    Find similar
                (768 dimensions)    (local file)      past messages
```

### Embedding Generation

- Uses **Google Gemini** to convert text to vectors
- Each message becomes a 768-dimensional vector
- Similar meanings = similar vectors

### Storage Process

1. **Message received** → Generate embedding
2. **Store in ChromaDB** → Local file database
3. **Index for search** → Fast similarity lookup

### Retrieval Process

1. **New message** → Generate query embedding
2. **Search ChromaDB** → Find similar vectors
3. **Return context** → Relevant past conversations

## 🚨 Troubleshooting

### Issue: "ChromaDB not found"

```bash
pip install chromadb==0.4.22
```

### Issue: "Embedding generation failed"

```bash
# Check your Google API key
python -c "import os; print('GOOGLE_API_KEY:', os.getenv('GOOGLE_API_KEY')[:10] + '...' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')"
```

### Issue: "Permission denied on data directory"

```bash
# Create the directory manually
mkdir -p ./data/vector_store
chmod 755 ./data/vector_store
```

### Issue: "Vector store initialization failed"

```python
# Check if ChromaDB can create a client
import chromadb
client = chromadb.PersistentClient(path="./test_db")
print("ChromaDB client created successfully!")
```

## 🔄 Switching to Vertex AI (Advanced)

If you want to use Google's managed vector database instead:

### 1. Set up Google Cloud

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable APIs

```bash
gcloud services enable aiplatform.googleapis.com
```

### 3. Update Environment

```bash
# Add to .env
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
USE_VERTEX_AI=true
```

### 4. Update Code

```python
# In your initialization
vector_store = VectorStore(
    persist_directory="./data/vector_store",  # Not used for Vertex
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    use_vertex=True  # Enable Vertex AI
)
```

## 📊 Performance Comparison

| Feature | ChromaDB (Local)     | Vertex AI (Cloud)        |
| ------- | -------------------- | ------------------------ |
| Setup   | ✅ Zero setup        | ⚠️ Google Cloud required |
| Cost    | ✅ Free              | 💰 Pay per query         |
| Speed   | ✅ Very fast (local) | ⚠️ Network latency       |
| Scale   | ⚠️ Single machine    | ✅ Unlimited             |
| Backup  | ⚠️ Manual            | ✅ Automatic             |

## 🎯 Recommendation

**For testing and development:** Use ChromaDB (default)
**For production at scale:** Consider Vertex AI

Your current setup with ChromaDB is perfect for testing all the memory system features!

## ✅ Verification Checklist

- [ ] ChromaDB installed (`pip install chromadb`)
- [ ] Google API key set for embeddings
- [ ] Data directory writable (`./data/vector_store`)
- [ ] Test script runs successfully
- [ ] Chat interface can store and retrieve memories

## 🚀 Ready to Test!

Your vector database is ready! Run the chat interface and start testing:

```bash
python chat_test_interface.py
```

The system will automatically:

1. Create the ChromaDB database
2. Generate embeddings for messages
3. Store vectors locally
4. Retrieve similar memories for context

No registration or external setup required! 🎉
