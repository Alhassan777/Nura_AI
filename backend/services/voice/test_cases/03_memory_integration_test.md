# Memory Integration Test

## Test Configuration

- **Name**: Memory Integration Test
- **Type**: Chat
- **Attempts**: 2

## Test Script

```
You are returning to discuss previous therapy goals.

[Background]
You've had previous conversations about coping strategies and want to build on them.

[Interaction Flow]
1. Say "Remember when we talked about my coping strategies last week?"
2. Reference specific techniques like breathing exercises
3. Ask for insights about your conversation patterns
4. Request the assistant store today's key discussion points

[Expectations]
The assistant should demonstrate continuity from past conversations.

[Expected Tools Usage]
- search_user_memories
- store_conversation_memory
- get_memory_insights
```

## Success Rubric

```
1. The assistant searches previous memories successfully
2. The assistant provides relevant context from past conversations
3. The assistant can store new conversation elements
4. The response shows continuity and personalization
5. The assistant offers insights based on conversation history
```

## What This Tests

- **Memory Search**: Semantic search capabilities in conversation history
- **Context Continuity**: Building on previous therapeutic relationships
- **Memory Storage**: Proper storage of important conversation elements
- **Personalization**: Tailored responses based on user history
- **Insight Generation**: AI analysis of conversation patterns

## Expected Flow

1. User references past conversations
2. Assistant searches memory for relevant context
3. Assistant provides relevant information from past sessions
4. User discusses new developments
5. Assistant stores key points from current conversation
6. Assistant offers insights based on patterns over time
