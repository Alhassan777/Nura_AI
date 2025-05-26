'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Send, User, Bot, AlertTriangle, CheckCircle, XCircle, Brain, Clock, Database, Trash2, RefreshCw, Shield } from 'lucide-react';
import MemoryPrivacyManager from '@/components/MemoryPrivacyManager';

interface ChatMessage {
  id: string;
  message: string;
  response: string;
  crisis_level: string;
  crisis_explanation: string;
  resources_provided: string[];
  coping_strategies: string[];
  memory_stored: boolean;
  timestamp: string;
  configuration_warning?: boolean;
  error?: string;
}

interface HealthStatus {
  status: string;
  memory_service?: any;
  error?: string;
  timestamp: string;
}

interface MemoryItem {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  metadata: {
    storage_type?: string;
    has_pii?: boolean;
    detected_items?: string[];
    score?: {
      relevance: number;
      stability: number;
      explicitness: number;
    };
    [key: string]: any;
  };
}

interface MemoryStats {
  total: number;
  short_term: number;
  long_term: number;
  sensitive: number;
}

interface MemoryContext {
  short_term: MemoryItem[];
  long_term: MemoryItem[];
  emotional_anchors?: MemoryItem[];
  digest: string;
}

export default function TestChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => `test-user-${Date.now()}`);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [activeTab, setActiveTab] = useState('chat');
  
  // Memory-related state
  const [memoryContext, setMemoryContext] = useState<MemoryContext | null>(null);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check health status on component mount
  useEffect(() => {
    checkHealthStatus();
  }, []);

  // Load memories when switching to memories tab
  useEffect(() => {
    if (activeTab === 'memories') {
      loadMemories();
    }
  }, [activeTab, userId]);

  const checkHealthStatus = async () => {
    try {
      const response = await fetch('/api/chat');
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({
        status: 'error',
        error: 'Failed to connect to chat service',
        timestamp: new Date().toISOString(),
      });
    }
  };

  const loadMemories = async () => {
    setIsLoadingMemories(true);
    try {
      // Fetch all long-term memories (both regular and emotional anchors)
      const allMemoriesResponse = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: `/memory/all-long-term?user_id=${userId}`,
          method: 'GET'
        }),
      });

      // Fetch short-term memories (context)
      const contextResponse = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: `/memory/context?user_id=${userId}`,
          method: 'POST',
          body: { query: '' }
        }),
      });

      if (allMemoriesResponse.ok && contextResponse.ok) {
        const allMemoriesData = await allMemoriesResponse.json();
        const contextData = await contextResponse.json();
        
        // Combine the data into the expected structure
        setMemoryContext({
          short_term: contextData.context?.short_term || [],
          long_term: allMemoriesData.regular_memories || [],
          emotional_anchors: allMemoriesData.emotional_anchors || [],
          digest: `${allMemoriesData.counts?.total || 0} total long-term memories found`
        });
      }

      // Fetch memory stats
      const statsResponse = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: `/memory/stats?user_id=${userId}`,
          method: 'GET'
        }),
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setMemoryStats(statsData.stats);
      }
    } catch (error) {
      console.error('Error loading memories:', error);
    } finally {
      setIsLoadingMemories(false);
    }
  };

  const clearMemories = async () => {
    if (!confirm('Are you sure you want to clear all memories? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: `/memory/forget?user_id=${userId}`,
          method: 'POST'
        }),
      });

      if (response.ok) {
        // Reload memories after clearing
        await loadMemories();
      } else {
        console.error('Failed to clear memories');
      }
    } catch (error) {
      console.error('Error clearing memories:', error);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    setIsLoading(true);
    const messageText = inputValue;
    setInputValue('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          user_id: userId,
          include_memory: true,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send message');
      }

      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        message: messageText,
        response: data.response,
        crisis_level: data.crisis_level,
        crisis_explanation: data.crisis_explanation,
        resources_provided: data.resources_provided || [],
        coping_strategies: data.coping_strategies || [],
        memory_stored: data.memory_stored,
        timestamp: data.timestamp,
        configuration_warning: data.configuration_warning,
      };

      setMessages(prev => [...prev, newMessage]);
      
      // If we're on the memories tab, refresh the memories
      if (activeTab === 'memories') {
        loadMemories();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        message: messageText,
        response: 'Sorry, I encountered an error. Please try again.',
        crisis_level: 'SUPPORT',
        crisis_explanation: 'Error occurred',
        resources_provided: [],
        coping_strategies: [],
        memory_stored: false,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getCrisisLevelColor = (level: string) => {
    switch (level) {
      case 'CRISIS': return 'bg-red-100 text-red-800 border-red-200';
      case 'CONCERN': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'SUPPORT': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getHealthStatusIcon = () => {
    if (!healthStatus) return <Loader2 className="h-4 w-4 animate-spin" />;
    
    switch (healthStatus.status) {
      case 'ok': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const renderMemoryItem = (memory: MemoryItem, type: 'short-term' | 'long-term') => (
    <div key={memory.id} className="border rounded-lg p-3 space-y-2">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm">{memory.content}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline" className="text-xs">
              {type}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {memory.type}
            </Badge>
            {memory.metadata.has_pii && (
              <Badge variant="destructive" className="text-xs">
                Contains PII
              </Badge>
            )}
          </div>
        </div>
      </div>
      
      <div className="text-xs text-gray-500 space-y-1">
        <div>Created: {formatTimestamp(memory.timestamp)}</div>
        {memory.metadata.score && (memory.metadata.score.relevance !== undefined || memory.metadata.score.stability !== undefined || memory.metadata.score.explicitness !== undefined) && (
          <div className="flex gap-4">
            <span>Relevance: {memory.metadata.score.relevance?.toFixed(2) || 'N/A'}</span>
            <span>Stability: {memory.metadata.score.stability?.toFixed(2) || 'N/A'}</span>
            <span>Explicitness: {memory.metadata.score.explicitness?.toFixed(2) || 'N/A'}</span>
          </div>
        )}
        {memory.metadata.detected_items && Array.isArray(memory.metadata.detected_items) && memory.metadata.detected_items.length > 0 && (
          <div>PII Types: {memory.metadata.detected_items.join(', ')}</div>
        )}
        
        {/* Debug section - show raw metadata */}
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
            🔍 Debug: Raw Memory Data
          </summary>
          <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32">
            {JSON.stringify(memory, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Nura Memory System Test Chat</h1>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          {getHealthStatusIcon()}
          <span>Service Status: {healthStatus?.status || 'checking...'}</span>
          <span className="text-xs">User ID: {userId}</span>
        </div>
        {healthStatus?.error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {healthStatus.error}
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="chat" className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            Chat
          </TabsTrigger>
          <TabsTrigger value="memories" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Memories
          </TabsTrigger>
          <TabsTrigger value="anchors" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Emotional Anchors
          </TabsTrigger>
          <TabsTrigger value="privacy" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Privacy
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chat Interface */}
            <div className="lg:col-span-2">
              <Card className="h-[600px] flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bot className="h-5 w-5" />
                    Chat with Nura
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col">
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    {messages.length === 0 && (
                      <div className="text-center text-gray-500 py-8">
                        <Bot className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                        <p>Start a conversation with Nura!</p>
                        <p className="text-sm">Try saying: "I'm feeling anxious today"</p>
                      </div>
                    )}
                    
                    {messages.map((msg) => (
                      <div key={msg.id} className="space-y-3">
                        {/* User Message */}
                        <div className="flex items-start gap-3">
                          <User className="h-6 w-6 mt-1 text-blue-500" />
                          <div className="flex-1">
                            <div className="bg-blue-50 p-3 rounded-lg">
                              <p>{msg.message}</p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Assistant Response */}
                        <div className="flex items-start gap-3">
                          <Bot className="h-6 w-6 mt-1 text-green-500" />
                          <div className="flex-1">
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p>{msg.response}</p>
                              
                              {/* Crisis Level Badge */}
                              <div className="mt-2 flex items-center gap-2">
                                <Badge className={getCrisisLevelColor(msg.crisis_level)}>
                                  {msg.crisis_level}
                                </Badge>
                                {msg.memory_stored && (
                                  <Badge variant="outline" className="text-xs">
                                    Memory Stored
                                  </Badge>
                                )}
                                {msg.configuration_warning && (
                                  <Badge variant="destructive" className="text-xs">
                                    Config Warning
                                  </Badge>
                                )}
                              </div>
                              
                              {/* Resources and Strategies */}
                              {(msg.resources_provided.length > 0 || msg.coping_strategies.length > 0) && (
                                <div className="mt-2 text-xs text-gray-600">
                                  {msg.resources_provided.length > 0 && (
                                    <div>Resources: {msg.resources_provided.join(', ')}</div>
                                  )}
                                  {msg.coping_strategies.length > 0 && (
                                    <div>Strategies: {msg.coping_strategies.join(', ')}</div>
                                  )}
                                </div>
                              )}
                              
                              {msg.error && (
                                <div className="mt-2 text-xs text-red-600">
                                  Error: {msg.error}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {isLoading && (
                      <div className="flex items-start gap-3">
                        <Bot className="h-6 w-6 mt-1 text-green-500" />
                        <div className="flex-1">
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <div className="flex items-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-gray-600">Nura is thinking...</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </div>
                  
                  {/* Input Form */}
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <Input
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Type your message..."
                      disabled={isLoading}
                      className="flex-1"
                    />
                    <Button type="submit" disabled={isLoading || !inputValue.trim()}>
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            {/* System Information */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">System Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Service:</span>
                    <span className={healthStatus?.status === 'ok' ? 'text-green-600' : 'text-red-600'}>
                      {healthStatus?.status || 'checking...'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Messages:</span>
                    <span>{messages.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>User ID:</span>
                    <span className="text-xs font-mono">{userId.slice(-8)}</span>
                  </div>
                  <Button 
                    onClick={checkHealthStatus} 
                    variant="outline" 
                    size="sm" 
                    className="w-full mt-2"
                  >
                    Refresh Status
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Test Scenarios</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm space-y-1">
                    <p className="font-medium">Try these messages:</p>
                    <ul className="text-xs space-y-1 text-gray-600">
                      <li><strong>Temporary states (short-term only):</strong></li>
                      <li>• "I'm feeling anxious today"</li>
                      <li>• "I've been really sad lately"</li>
                      <li>• "I'm having trouble sleeping"</li>
                      <li><strong>Lasting memories (long-term):</strong></li>
                      <li>• "I got into Harvard today"</li>
                      <li>• "I realized I get anxious when my mom calls"</li>
                      <li><strong>Emotional anchors:</strong></li>
                      <li>• "My grandmother's garden represents peace to me"</li>
                      <li>• "Playing piano helps me express emotions"</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {healthStatus?.memory_service && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Memory Service</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
                      {JSON.stringify(healthStatus.memory_service, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="memories" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Memory Statistics */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Memory Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {isLoadingMemories ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading...</span>
                    </div>
                  ) : memoryStats ? (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Total Memories:</span>
                        <span className="font-medium">{memoryStats.total}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Short-term:</span>
                        <span className="font-medium">{memoryStats.short_term}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Long-term:</span>
                        <span className="font-medium">{memoryStats.long_term}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Sensitive:</span>
                        <span className="font-medium text-red-600">{memoryStats.sensitive}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">No statistics available</div>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={loadMemories} 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      disabled={isLoadingMemories}
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Refresh
                    </Button>
                    <Button 
                      onClick={clearMemories} 
                      variant="destructive" 
                      size="sm" 
                      className="flex-1"
                      disabled={isLoadingMemories}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Clear All
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Memory Lists */}
            <div className="lg:col-span-2 space-y-6">
              {/* Short-term Memories */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Short-term Memories
                    {memoryContext?.short_term && (
                      <Badge variant="outline">{memoryContext.short_term.length}</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingMemories ? (
                    <div className="flex items-center gap-2 py-4">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading memories...</span>
                    </div>
                  ) : memoryContext?.short_term && memoryContext.short_term.length > 0 ? (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {memoryContext.short_term.map((memory) => 
                        renderMemoryItem(memory, 'short-term')
                      )}
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Clock className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                      <p>No short-term memories found</p>
                      <p className="text-sm">Start a conversation to create memories</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Long-term Memories */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Long-term Memories
                    {memoryContext?.long_term && (
                      <Badge variant="outline">{memoryContext.long_term.length}</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingMemories ? (
                    <div className="flex items-center gap-2 py-4">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading memories...</span>
                    </div>
                  ) : memoryContext?.long_term && memoryContext.long_term.length > 0 ? (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {memoryContext.long_term.map((memory) => 
                        renderMemoryItem(memory, 'long-term')
                      )}
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Database className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                      <p>No long-term memories found</p>
                      <p className="text-sm">Memories with high stability scores will appear here</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Memory Digest */}
              {memoryContext?.digest && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Memory Digest</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-700">{memoryContext.digest}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="anchors" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Emotional Anchors Statistics */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Emotional Anchors
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {isLoadingMemories ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading...</span>
                    </div>
                  ) : memoryContext?.emotional_anchors ? (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Total Anchors:</span>
                        <span className="font-medium">{memoryContext.emotional_anchors.length}</span>
                      </div>
                      <div className="text-xs text-gray-600">
                        <p>Meaningful connections that serve as emotional touchstones and coping resources.</p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">No anchors available</div>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={loadMemories} 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      disabled={isLoadingMemories}
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Refresh
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Anchor Categories */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Anchor Types</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-xs space-y-1 text-gray-600">
                    <div>🏛️ <strong>Beliefs:</strong> Core values & philosophies</div>
                    <div>⚓ <strong>Anchors:</strong> Places of safety & comfort</div>
                    <div>🎨 <strong>Creative:</strong> Artistic expressions</div>
                    <div>🔮 <strong>Symbolic:</strong> Meaningful symbols</div>
                    <div>🌊 <strong>Metaphors:</strong> Personal metaphors</div>
                    <div>📍 <strong>Places:</strong> Sacred locations</div>
                    <div>💎 <strong>Objects:</strong> Meaningful items</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Emotional Anchors List */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Your Emotional Anchors
                    {memoryContext?.emotional_anchors && (
                      <Badge variant="outline">{memoryContext.emotional_anchors.length}</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingMemories ? (
                    <div className="flex items-center gap-2 py-4">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading emotional anchors...</span>
                    </div>
                  ) : memoryContext?.emotional_anchors && memoryContext.emotional_anchors.length > 0 ? (
                    <div className="space-y-4 max-h-[600px] overflow-y-auto">
                      {memoryContext.emotional_anchors.map((anchor) => (
                        <div key={anchor.id} className="border rounded-lg p-4 space-y-3 bg-gradient-to-r from-blue-50 to-purple-50">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium">{anchor.content}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="secondary" className="text-xs">
                                  {anchor.metadata.connection_type || 'anchor'}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {anchor.metadata.anchor_strength || 'developing'}
                                </Badge>
                                {anchor.metadata.has_pii && (
                                  <Badge variant="destructive" className="text-xs">
                                    Contains PII
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* Emotional Significance */}
                          {anchor.metadata.emotional_significance && (
                            <div className="bg-white/50 rounded p-2">
                              <div className="text-xs font-medium text-gray-700">Emotional Significance:</div>
                              <div className="text-xs text-gray-600">{anchor.metadata.emotional_significance}</div>
                            </div>
                          )}
                          
                          {/* Personal Meaning */}
                          {anchor.metadata.personal_meaning && (
                            <div className="bg-white/50 rounded p-2">
                              <div className="text-xs font-medium text-gray-700">Personal Meaning:</div>
                              <div className="text-xs text-gray-600">{anchor.metadata.personal_meaning}</div>
                            </div>
                          )}
                          
                          <div className="text-xs text-gray-500 space-y-1">
                            <div>Created: {formatTimestamp(anchor.timestamp)}</div>
                            {anchor.metadata.score && (anchor.metadata.score.relevance !== undefined || anchor.metadata.score.stability !== undefined || anchor.metadata.score.explicitness !== undefined) && (
                              <div className="flex gap-4">
                                <span>Relevance: {anchor.metadata.score.relevance?.toFixed(2) || 'N/A'}</span>
                                <span>Stability: {anchor.metadata.score.stability?.toFixed(2) || 'N/A'}</span>
                                <span>Explicitness: {anchor.metadata.score.explicitness?.toFixed(2) || 'N/A'}</span>
                              </div>
                            )}
                            
                            {/* Debug section for anchors */}
                            <details className="mt-2">
                              <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
                                🔍 Debug: Raw Anchor Data
                              </summary>
                              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32">
                                {JSON.stringify(anchor, null, 2)}
                              </pre>
                            </details>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Database className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                      <p>No emotional anchors found</p>
                      <p className="text-sm">Share meaningful connections, beliefs, or symbols that bring you comfort</p>
                      <div className="mt-4 text-xs text-gray-400">
                        <p>Try saying things like:</p>
                        <ul className="mt-1 space-y-1">
                          <li>• "My grandmother's garden represents peace to me"</li>
                          <li>• "Playing piano helps me express my emotions"</li>
                          <li>• "The ocean reminds me that problems are temporary"</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="privacy" className="mt-6">
          <MemoryPrivacyManager userId={userId} />
        </TabsContent>
      </Tabs>
    </div>
  );
} 