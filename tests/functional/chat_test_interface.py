#!/usr/bin/env python3
"""
Simple Chat Interface for Testing Nura Memory System

This provides a web interface to test all memory functionalities:
- Memory storage and retrieval
- PII detection and consent
- Context-aware conversations
- ML-based filtering
- Dual storage strategy
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import our memory system
import sys
import os

sys.path.append("src")

from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem
from services.memory.assistant.mental_health_assistant import MentalHealthAssistant

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize services
app = FastAPI(title="Nura Memory System Test Interface")
memory_service = MemoryService()
assistant = MentalHealthAssistant()


# Pydantic models
class ChatMessage(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    memory_stored: bool
    context_used: List[str]
    pii_detected: List[Dict[str, Any]]
    filtering_result: Dict[str, Any]
    storage_strategy: str


class MemoryStats(BaseModel):
    short_term_count: int
    long_term_count: int
    total_memories: int


# Store for demo purposes (in production, use proper session management)
user_sessions = {}


@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface HTML."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nura Memory System Test Chat</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container { 
                display: grid; 
                grid-template-columns: 2fr 1fr; 
                gap: 20px; 
                height: 80vh;
            }
            .chat-container { 
                background: white; 
                border-radius: 10px; 
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .info-panel { 
                background: white; 
                border-radius: 10px; 
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow-y: auto;
            }
            .chat-messages { 
                height: 400px; 
                overflow-y: auto; 
                border: 1px solid #ddd; 
                padding: 10px; 
                margin-bottom: 10px;
                background-color: #fafafa;
                border-radius: 5px;
            }
            .message { 
                margin: 10px 0; 
                padding: 10px; 
                border-radius: 5px; 
            }
            .user-message { 
                background-color: #e3f2fd; 
                text-align: right; 
            }
            .assistant-message { 
                background-color: #f1f8e9; 
            }
            .system-message { 
                background-color: #fff3e0; 
                font-style: italic; 
                font-size: 0.9em;
            }
            .input-container { 
                display: flex; 
                gap: 10px; 
            }
            input[type="text"] { 
                flex: 1; 
                padding: 10px; 
                border: 1px solid #ddd; 
                border-radius: 5px;
            }
            button { 
                padding: 10px 20px; 
                background-color: #2196F3; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
            }
            button:hover { 
                background-color: #1976D2; 
            }
            .stats { 
                background-color: #f8f9fa; 
                padding: 10px; 
                border-radius: 5px; 
                margin-bottom: 10px;
            }
            .pii-info { 
                background-color: #fff3cd; 
                padding: 10px; 
                border-radius: 5px; 
                margin-bottom: 10px;
                border-left: 4px solid #ffc107;
            }
            .memory-info { 
                background-color: #d1ecf1; 
                padding: 10px; 
                border-radius: 5px; 
                margin-bottom: 10px;
                border-left: 4px solid #17a2b8;
            }
            .user-id-input {
                margin-bottom: 20px;
            }
            .user-id-input input {
                width: 200px;
            }
            h1, h2, h3 { color: #333; }
            .feature-list {
                background-color: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .feature-list ul {
                margin: 0;
                padding-left: 20px;
            }
        </style>
    </head>
    <body>
        <h1>🧠 Nura Memory System Test Interface</h1>
        
                    <div class="feature-list">
                <h3>🚀 Features Being Tested:</h3>
                <ul>
                    <li><strong>Significance-Based Scoring:</strong> Human-centered memory evaluation</li>
                    <li><strong>Crisis Detection:</strong> Catches indirect expressions</li>
                    <li><strong>PII Detection:</strong> 10+ categories with granular consent</li>
                    <li><strong>Dual Storage:</strong> Redis (short-term) + ChromaDB (long-term)</li>
                    <li><strong>Context Awareness:</strong> Memory-based conversations</li>
                </ul>
            </div>

        <div class="container">
            <div class="chat-container">
                <div class="user-id-input">
                    <label for="userId">User ID:</label>
                    <input type="text" id="userId" value="test_user_123" placeholder="Enter user ID">
                    <button onclick="clearChat()">Clear Chat</button>
                    <button onclick="getMemoryStats()">Get Memory Stats</button>
                </div>
                
                <div class="chat-messages" id="chatMessages"></div>
                
                <div class="input-container">
                    <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <div class="info-panel">
                <h3>📊 System Information</h3>
                <div id="memoryStats" class="stats">
                    <strong>Memory Stats:</strong><br>
                    Short-term: 0<br>
                    Long-term: 0<br>
                    Total: 0
                </div>
                
                <div id="lastPiiInfo" class="pii-info" style="display: none;">
                    <strong>🔒 PII Detected:</strong><br>
                    <span id="piiDetails">None</span>
                </div>
                
                <div id="lastMemoryInfo" class="memory-info" style="display: none;">
                    <strong>🧠 Memory Processing:</strong><br>
                    <span id="memoryDetails">None</span>
                </div>

                <h3>🧪 Test Scenarios</h3>
                <div style="font-size: 0.9em;">
                    <p><strong>Crisis Detection:</strong></p>
                    <ul>
                        <li>"I want to end it all"</li>
                        <li>"Everyone would be better off without me"</li>
                        <li>"I feel like I'm at the end of my rope"</li>
                    </ul>
                    
                    <p><strong>Significant Memories:</strong></p>
                    <ul>
                        <li>"I got into Harvard today, my dream college"</li>
                        <li>"I met the love of my life today"</li>
                        <li>"I realized I get anxious when my mom calls"</li>
                    </ul>
                    
                    <p><strong>PII Detection:</strong></p>
                    <ul>
                        <li>"My name is Sarah Johnson"</li>
                        <li>"I take Zoloft for my depression"</li>
                        <li>"My therapist Dr. Martinez said..."</li>
                    </ul>
                </div>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const userId = document.getElementById('userId').value;
                const messageInput = document.getElementById('messageInput');
                const message = messageInput.value.trim();
                
                if (!message || !userId) return;
                
                // Add user message to chat
                addMessage(message, 'user');
                messageInput.value = '';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: userId,
                            message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Add assistant response
                    addMessage(data.response, 'assistant');
                    
                    // Add system information
                    if (data.memory_stored || data.context_used.length > 0 || data.pii_detected.length > 0) {
                        let systemInfo = [];
                        if (data.memory_stored) systemInfo.push("✅ Memory stored");
                        if (data.context_used.length > 0) systemInfo.push(`🧠 Used ${data.context_used.length} memories for context`);
                        if (data.pii_detected.length > 0) systemInfo.push(`🔒 Detected ${data.pii_detected.length} PII items`);
                        systemInfo.push(`📊 Filter: ${data.filtering_result.reason}`);
                        systemInfo.push(`💾 Storage: ${data.storage_strategy}`);
                        
                        addMessage(systemInfo.join(' | '), 'system');
                    }
                    
                    // Update info panels
                    updatePiiInfo(data.pii_detected);
                    updateMemoryInfo(data);
                    
                } catch (error) {
                    addMessage('Error: ' + error.message, 'system');
                }
            }
            
            function addMessage(message, type) {
                const chatMessages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}-message`;
                messageDiv.textContent = message;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function updatePiiInfo(piiDetected) {
                const piiInfo = document.getElementById('lastPiiInfo');
                const piiDetails = document.getElementById('piiDetails');
                
                if (piiDetected.length > 0) {
                    piiInfo.style.display = 'block';
                    piiDetails.innerHTML = piiDetected.map(item => 
                        `${item.entity_type}: "${item.text}" (${(item.confidence * 100).toFixed(1)}%)`
                    ).join('<br>');
                } else {
                    piiInfo.style.display = 'none';
                }
            }
            
            function updateMemoryInfo(data) {
                const memoryInfo = document.getElementById('lastMemoryInfo');
                const memoryDetails = document.getElementById('memoryDetails');
                
                memoryInfo.style.display = 'block';
                memoryDetails.innerHTML = `
                    Filter: ${data.filtering_result.reason}<br>
                    Confidence: ${data.filtering_result.confidence}<br>
                    Storage: ${data.storage_strategy}<br>
                    Context Used: ${data.context_used.length} memories
                `;
            }
            
            async function getMemoryStats() {
                const userId = document.getElementById('userId').value;
                if (!userId) return;
                
                try {
                    const response = await fetch(`/memory/stats/${userId}`);
                    const stats = await response.json();
                    
                    document.getElementById('memoryStats').innerHTML = `
                        <strong>Memory Stats:</strong><br>
                        Short-term: ${stats.short_term_count}<br>
                        Long-term: ${stats.long_term_count}<br>
                        Total: ${stats.total_memories}
                    `;
                } catch (error) {
                    console.error('Error getting memory stats:', error);
                }
            }
            
            function clearChat() {
                document.getElementById('chatMessages').innerHTML = '';
                document.getElementById('lastPiiInfo').style.display = 'none';
                document.getElementById('lastMemoryInfo').style.display = 'none';
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // Auto-focus on message input
            document.getElementById('messageInput').focus();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_msg: ChatMessage):
    """Main chat endpoint that demonstrates all memory system features."""
    try:
        logger.info(f"Processing chat message from user {chat_msg.user_id}")

        # 1. Store user message FIRST so it's available for context
        user_storage_result = await memory_service.process_memory(
            user_id=chat_msg.user_id,
            content=chat_msg.message,
            type="user_message",
            metadata={"source": "chat_interface"},
        )

        # 2. Get conversation context from memory (now includes the current message)
        memory_context = await memory_service.get_memory_context(
            user_id=chat_msg.user_id, query=chat_msg.message
        )
        context_memories = memory_context.short_term + memory_context.long_term

        context_texts = [memory.content for memory in context_memories]
        logger.info(f"Retrieved {len(context_texts)} context memories")

        # 3. Generate AI response using context
        ai_response_data = await assistant.generate_response(
            user_message=chat_msg.message,
            memory_context=memory_context,
            user_id=chat_msg.user_id,
        )
        ai_response = ai_response_data["response"]

        # 4. Store AI response
        ai_storage_result = await memory_service.process_memory(
            user_id=chat_msg.user_id,
            content=ai_response,
            type="assistant_message",
            metadata={"source": "chat_interface"},
        )

        # 5. Extract detailed information for the interface
        pii_summary = user_storage_result.get("pii_summary", {})
        pii_detected = pii_summary.get("types", [])
        storage_details = user_storage_result.get("storage_details", {})
        storage_strategy = storage_details.get("privacy_strategy", "unknown")
        memory_stored = user_storage_result.get("stored", False)

        # Create a filtering result from the score information
        score_info = user_storage_result.get("score", {})
        filtering_result = {
            "reason": (
                "Memory processed successfully"
                if memory_stored
                else "Memory not stored"
            ),
            "confidence": score_info.get("relevance", 0.0),
            "score": score_info,
        }

        return ChatResponse(
            response=ai_response,
            memory_stored=memory_stored,
            context_used=context_texts,
            pii_detected=pii_detected,
            filtering_result=filtering_result,
            storage_strategy=storage_strategy,
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/memory/stats/{user_id}", response_model=MemoryStats)
async def get_memory_stats(user_id: str):
    """Get memory statistics for a user."""
    try:
        # Use the proper memory service stats method
        stats = await memory_service.get_memory_stats(user_id)

        return MemoryStats(
            short_term_count=stats.short_term,
            long_term_count=stats.long_term,
            total_memories=stats.total,
        )

    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        return MemoryStats(short_term_count=0, long_term_count=0, total_memories=0)


@app.post("/vector/add")
async def add_to_vector_store(request: dict):
    """Directly add a memory to the vector store for testing."""
    try:
        user_id = request.get("user_id")
        content = request.get("content")
        memory_type = request.get("type", "test")

        if not user_id or not content:
            raise HTTPException(
                status_code=400, detail="user_id and content are required"
            )

        # Create a memory item
        memory = MemoryItem(
            id=str(uuid.uuid4()),
            userId=user_id,
            content=content,
            type=memory_type,
            metadata={"source": "direct_api", "test": True},
            timestamp=datetime.utcnow(),
        )

        # Add directly to vector store
        await memory_service.vector_store.add_memory(user_id, memory)

        return {
            "success": True,
            "memory_id": memory.id,
            "message": "Memory added to vector store",
            "content": content,
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error adding to vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector store error: {str(e)}")


@app.get("/vector/query/{user_id}")
async def query_vector_store(user_id: str, query: str, limit: int = 5):
    """Directly query the vector store for testing."""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="query parameter is required")

        # Query vector store directly
        memories = await memory_service.vector_store.get_similar_memories(
            user_id=user_id, query=query, limit=limit
        )

        return {
            "success": True,
            "query": query,
            "user_id": user_id,
            "results_count": len(memories),
            "memories": [
                {
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.type,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata,
                }
                for memory in memories
            ],
        }

    except Exception as e:
        logger.error(f"Error querying vector store: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Vector store query error: {str(e)}"
        )


@app.get("/vector/count/{user_id}")
async def get_vector_store_count(user_id: str):
    """Get the count of memories in vector store for a user."""
    try:
        count = await memory_service.vector_store.get_memory_count(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "count": count,
            "message": f"Found {count} memories in vector store",
        }

    except Exception as e:
        logger.error(f"Error getting vector store count: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Vector store count error: {str(e)}"
        )


@app.delete("/vector/clear/{user_id}")
async def clear_vector_store(user_id: str):
    """Clear all memories from vector store for a user."""
    try:
        await memory_service.vector_store.clear_memories(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "message": "Vector store cleared for user",
        }

    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Vector store clear error: {str(e)}"
        )


@app.post("/redis/add")
async def add_to_redis_store(request: dict):
    """Directly add a memory to Redis for testing."""
    try:
        user_id = request.get("user_id")
        content = request.get("content")
        memory_type = request.get("type", "test")

        if not user_id or not content:
            raise HTTPException(
                status_code=400, detail="user_id and content are required"
            )

        # Create a memory item
        memory = MemoryItem(
            id=str(uuid.uuid4()),
            userId=user_id,
            content=content,
            type=memory_type,
            metadata={"source": "direct_api", "test": True},
            timestamp=datetime.utcnow(),
        )

        # Add directly to Redis
        await memory_service.redis_store.add_memory(user_id, memory)

        return {
            "success": True,
            "memory_id": memory.id,
            "message": "Memory added to Redis store",
            "content": content,
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error adding to Redis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")


@app.get("/redis/get/{user_id}")
async def get_redis_memories(user_id: str, limit: int = 10):
    """Get memories from Redis for a user."""
    try:
        memories = await memory_service.redis_store.get_memories(user_id)

        # Limit results
        limited_memories = memories[:limit]

        return {
            "success": True,
            "user_id": user_id,
            "total_count": len(memories),
            "returned_count": len(limited_memories),
            "memories": [
                {
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.type,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata,
                }
                for memory in limited_memories
            ],
        }

    except Exception as e:
        logger.error(f"Error getting Redis memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis get error: {str(e)}")


@app.delete("/redis/clear/{user_id}")
async def clear_redis_store(user_id: str):
    """Clear all memories from Redis for a user."""
    try:
        await memory_service.redis_store.clear_memories(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "message": "Redis store cleared for user",
        }

    except Exception as e:
        logger.error(f"Error clearing Redis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis clear error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Redis connection
        redis_status = "connected"
        try:
            await memory_service.redis_store.redis.ping()
        except:
            redis_status = "disconnected"

        # Test vector store
        vector_status = "connected"
        try:
            # Simple test - this will create the collection if it doesn't exist
            await memory_service.vector_store.get_similar_memories(
                "health_check", "test", limit=1
            )
        except:
            vector_status = "disconnected"

        return {
            "status": "healthy",
            "redis": redis_status,
            "vector_store": vector_status,
            "ml_models": memory_service.quick_filter.use_ml_models,
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting Nura Memory System Test Interface...")
    print("📝 Features being tested:")
    print("   • Significance-based memory scoring")
    print("   • Crisis detection (indirect expressions)")
    print("   • PII detection (10+ categories)")
    print("   • Dual storage (Redis + ChromaDB)")
    print("   • Context-aware conversations")
    print()
    print("🌐 Open your browser to: http://localhost:8000")
    print("🧪 Try the test scenarios in the interface!")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
