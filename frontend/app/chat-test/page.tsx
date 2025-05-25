'use client';

import { useState, useEffect, useRef } from 'react';

interface BackendHealth {
  status: string;
  message: string;
  configuration: {
    has_configuration_issues: boolean;
    missing_required: string[];
    missing_optional: string[];
    status: string;
    message: string;
  };
  timestamp: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: any;
}

interface TestResult {
  endpoint: string;
  method: string;
  status: number;
  response: any;
  error?: string;
  timestamp: string;
  duration: number;
}

interface MemoryStats {
  total_memories: number;
  short_term_count: number;
  long_term_count: number;
  average_score: number;
  last_updated: string;
}

export default function ChatTestPage() {
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState('assistant');
  const [userId, setUserId] = useState('test-user-123');
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [includeMemory, setIncludeMemory] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const pipelines = [
    { id: 'assistant', name: 'Mental Health Assistant', endpoint: '/chat/assistant', description: 'Full AI assistant with crisis detection and memory integration' },
    { id: 'chat', name: 'Basic Chat', endpoint: '/chat', description: 'Simple chat processing with memory storage' },
    { id: 'dual-storage', name: 'Dual Storage', endpoint: '/memory/dual-storage', description: 'Advanced memory storage with consent management' },
    { id: 'memory-context', name: 'Memory Context', endpoint: '/memory/context', description: 'Retrieve relevant memory context' },
    { id: 'crisis-resources', name: 'Crisis Resources', endpoint: '/chat/crisis-resources', description: 'Get crisis intervention resources' },
  ];

  const testMessages = [
    { text: "I'm feeling really anxious today", category: "Anxiety" },
    { text: "I can't stop thinking about hurting myself", category: "Crisis" },
    { text: "I had a great day at work today!", category: "Positive" },
    { text: "My name is John and I live at 123 Main St", category: "PII" },
    { text: "I've been taking medication for depression", category: "Medical" },
    { text: "I feel hopeless and don't want to live anymore", category: "Severe Crisis" },
    { text: "Can you help me with coping strategies?", category: "Support Request" },
    { text: "I'm having trouble sleeping lately", category: "Sleep Issues" },
  ];

  useEffect(() => {
    checkBackendHealth();
    if (autoRefresh) {
      const interval = setInterval(checkBackendHealth, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (backendHealth?.status === 'healthy' || backendHealth?.status === 'degraded') {
      fetchMemoryStats();
    }
  }, [backendHealth, userId]);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          endpoint: '/health',
          method: 'GET'
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setBackendHealth(data);
      } else {
        setBackendHealth(null);
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setBackendHealth(null);
    }
  };

  const fetchMemoryStats = async () => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          endpoint: `/memory/stats?user_id=${userId}`,
          method: 'GET'
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setMemoryStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch memory stats:', error);
    }
  };

  const addTestResult = (result: TestResult) => {
    setTestResults(prev => [result, ...prev.slice(0, 19)]); // Keep last 20 results
  };

  const sendMessage = async (messageText: string = currentMessage) => {
    if (!messageText.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    const startTime = Date.now();

    try {
      let endpoint = '';
      let requestBody: any = {};

      switch (selectedPipeline) {
        case 'assistant':
          endpoint = `/chat/assistant?user_id=${userId}`;
          requestBody = {
            message: messageText,
            include_memory: includeMemory
          };
          break;
        case 'chat':
          endpoint = `/chat?user_id=${userId}`;
          requestBody = {
            content: messageText,
            type: 'chat'
          };
          break;
        case 'dual-storage':
          endpoint = `/memory/dual-storage?user_id=${userId}`;
          requestBody = {
            content: messageText,
            type: 'chat'
          };
          break;
        case 'memory-context':
          endpoint = `/memory/context?user_id=${userId}`;
          requestBody = {
            query: messageText
          };
          break;
        case 'crisis-resources':
          endpoint = '/chat/crisis-resources';
          requestBody = {};
          break;
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          endpoint,
          method: 'POST',
          body: requestBody
        }),
      });

      const duration = Date.now() - startTime;
      const data = await response.json();

      const testResult: TestResult = {
        endpoint,
        method: 'POST',
        status: response.status,
        response: data,
        timestamp: new Date().toISOString(),
        duration
      };

      if (!response.ok) {
        testResult.error = data.error || 'Unknown error';
      }

      addTestResult(testResult);

      if (response.ok) {
        let assistantMessage: ChatMessage;

        switch (selectedPipeline) {
          case 'assistant':
            assistantMessage = {
              id: (Date.now() + 1).toString(),
              type: 'assistant',
              content: data.response,
              timestamp: new Date().toISOString(),
              metadata: {
                crisis_level: data.crisis_level,
                crisis_explanation: data.crisis_explanation,
                resources_provided: data.resources_provided,
                coping_strategies: data.coping_strategies,
                memory_stored: data.memory_stored
              }
            };
            break;
          case 'dual-storage':
            assistantMessage = {
              id: (Date.now() + 1).toString(),
              type: 'system',
              content: data.needs_consent 
                ? `Consent required for storing: ${JSON.stringify(data.consent_options, null, 2)}`
                : `Memory processed: ${data.stored ? 'Stored' : 'Not stored'} - ${data.reason}`,
              timestamp: new Date().toISOString(),
              metadata: data
            };
            break;
          case 'memory-context':
            assistantMessage = {
              id: (Date.now() + 1).toString(),
              type: 'system',
              content: `Memory context retrieved: ${data.context.relevant_memories.length} memories found`,
              timestamp: new Date().toISOString(),
              metadata: data.context
            };
            break;
          case 'crisis-resources':
            assistantMessage = {
              id: (Date.now() + 1).toString(),
              type: 'system',
              content: `Crisis resources: ${JSON.stringify(data, null, 2)}`,
              timestamp: new Date().toISOString(),
              metadata: data
            };
            break;
          default:
            assistantMessage = {
              id: (Date.now() + 1).toString(),
              type: 'assistant',
              content: JSON.stringify(data, null, 2),
              timestamp: new Date().toISOString(),
              metadata: data
            };
        }

        setMessages(prev => [...prev, assistantMessage]);
        
        // Refresh memory stats after processing
        if (selectedPipeline === 'assistant' || selectedPipeline === 'chat' || selectedPipeline === 'dual-storage') {
          setTimeout(fetchMemoryStats, 1000);
        }
      } else {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'system',
          content: `Error: ${data.error || 'Unknown error occurred'}`,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `Network error: ${error}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const runAllTests = async () => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'system',
      content: '🧪 Running comprehensive test suite...',
      timestamp: new Date().toISOString(),
    }]);

    for (const message of testMessages) {
      for (const pipeline of pipelines) {
        setSelectedPipeline(pipeline.id);
        await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between tests
        await sendMessage(`[${message.category}] ${message.text}`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for response
      }
    }

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'system',
      content: '✅ Test suite completed!',
      timestamp: new Date().toISOString(),
    }]);
  };

  const clearMemory = async () => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          endpoint: `/memory/forget?user_id=${userId}`,
          method: 'POST',
          body: {}
        }),
      });

      if (response.ok) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: '🗑️ Memory cleared successfully',
          timestamp: new Date().toISOString(),
        }]);
        fetchMemoryStats();
      }
    } catch (error) {
      console.error('Failed to clear memory:', error);
    }
  };

  const exportMemory = async () => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          endpoint: `/memory/export?user_id=${userId}`,
          method: 'POST',
          body: {}
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `memory-export-${userId}-${new Date().toISOString()}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export memory:', error);
    }
  };

  const getCrisisLevelColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-orange-600 bg-orange-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🧠 Nura Memory Service - Comprehensive Test Interface
          </h1>
          
          {/* Backend Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Backend Status</h3>
              {backendHealth ? (
                <div>
                  <div className={`inline-block px-2 py-1 rounded text-sm ${
                    backendHealth.status === 'healthy' ? 'bg-green-100 text-green-800' :
                    backendHealth.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {backendHealth.status.toUpperCase()}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{backendHealth.message}</p>
                  {backendHealth.configuration.has_configuration_issues && (
                    <div className="mt-2 text-xs">
                      <p className="text-red-600">Missing Required: {backendHealth.configuration.missing_required.join(', ')}</p>
                      <p className="text-orange-600">Missing Optional: {backendHealth.configuration.missing_optional.length} items</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-red-600">❌ Backend Offline</div>
              )}
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Memory Statistics</h3>
              {memoryStats ? (
                <div className="text-sm">
                  <p>Total: {memoryStats.total_memories}</p>
                  <p>Short-term: {memoryStats.short_term_count}</p>
                  <p>Long-term: {memoryStats.long_term_count}</p>
                  <p>Avg Score: {memoryStats.average_score?.toFixed(2) || 'N/A'}</p>
                </div>
              ) : (
                <div className="text-gray-500">No data</div>
              )}
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Test Results</h3>
              <div className="text-sm">
                <p>Total Tests: {testResults.length}</p>
                <p>Success: {testResults.filter(r => r.status < 400).length}</p>
                <p>Errors: {testResults.filter(r => r.status >= 400).length}</p>
                <p>Avg Duration: {testResults.length > 0 ? Math.round(testResults.reduce((a, b) => a + b.duration, 0) / testResults.length) : 0}ms</p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pipeline</label>
              <select 
                value={selectedPipeline} 
                onChange={(e) => setSelectedPipeline(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                {pipelines.map(pipeline => (
                  <option key={pipeline.id} value={pipeline.id}>
                    {pipeline.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {pipelines.find(p => p.id === selectedPipeline)?.description}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="test-user-123"
              />
            </div>

            <div className="flex flex-col justify-end">
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeMemory}
                    onChange={(e) => setIncludeMemory(e.target.checked)}
                    className="mr-1"
                  />
                  <span className="text-sm">Include Memory</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="mr-1"
                  />
                  <span className="text-sm">Auto Refresh</span>
                </label>
              </div>
            </div>

            <div className="flex flex-col justify-end">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>
            </div>
          </div>

          {/* Quick Test Buttons */}
          <div className="mb-6">
            <h3 className="font-semibold mb-2">Quick Tests</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {testMessages.map((msg, index) => (
                <button
                  key={index}
                  onClick={() => sendMessage(msg.text)}
                  disabled={isLoading}
                  className="px-3 py-2 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 disabled:opacity-50"
                >
                  {msg.category}
                </button>
              ))}
            </div>
            <div className="flex space-x-2 mt-2">
              <button
                onClick={runAllTests}
                disabled={isLoading}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                🧪 Run All Tests
              </button>
              <button
                onClick={clearMemory}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                🗑️ Clear Memory
              </button>
              <button
                onClick={exportMemory}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                📥 Export Memory
              </button>
              <button
                onClick={checkBackendHealth}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                🔄 Refresh Status
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Chat Interface</h2>
            
            <div className="h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 mb-4 bg-gray-50">
              {messages.map((message) => (
                <div key={message.id} className={`mb-4 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                  <div className={`inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : message.type === 'system'
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-200 text-gray-900'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    {message.metadata && (
                      <div className="mt-2 text-xs opacity-75">
                        {message.metadata.crisis_level && (
                          <div className={`inline-block px-2 py-1 rounded mb-1 ${getCrisisLevelColor(message.metadata.crisis_level)}`}>
                            Crisis: {message.metadata.crisis_level}
                          </div>
                        )}
                        {message.metadata.crisis_explanation && (
                          <p>Explanation: {message.metadata.crisis_explanation}</p>
                        )}
                        {message.metadata.resources_provided && message.metadata.resources_provided.length > 0 && (
                          <p>Resources: {message.metadata.resources_provided.join(', ')}</p>
                        )}
                        {message.metadata.coping_strategies && message.metadata.coping_strategies.length > 0 && (
                          <p>Strategies: {message.metadata.coping_strategies.join(', ')}</p>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <p className="text-sm text-gray-500 mt-2">Processing...</p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="flex space-x-2">
              <input
                type="text"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                placeholder="Type your message..."
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={() => sendMessage()}
                disabled={isLoading || !currentMessage.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>

          {/* Test Results Panel */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Test Results</h2>
            
            <div className="h-96 overflow-y-auto">
              {testResults.map((result, index) => (
                <div key={index} className="mb-4 p-3 border border-gray-200 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium">{result.endpoint}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      result.status < 400 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {result.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    {new Date(result.timestamp).toLocaleTimeString()} • {result.duration}ms
                  </div>
                  {result.error && (
                    <div className="text-xs text-red-600 mb-2">
                      Error: {result.error}
                    </div>
                  )}
                  {showAdvanced && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-blue-600">Response Details</summary>
                      <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto">
                        {JSON.stringify(result.response, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
              {testResults.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  No test results yet. Send a message to start testing!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 