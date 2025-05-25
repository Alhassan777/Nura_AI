'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, User, Bot, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

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

export default function TestChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => `test-user-${Date.now()}`);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check health status on component mount
  useEffect(() => {
    checkHealthStatus();
  }, []);

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

  return (
    <div className="container mx-auto p-4 max-w-4xl">
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
                  <li>• "I'm feeling anxious today"</li>
                  <li>• "I've been really sad lately"</li>
                  <li>• "I'm having trouble sleeping"</li>
                  <li>• "I feel overwhelmed at work"</li>
                  <li>• "I'm having thoughts of self-harm"</li>
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
    </div>
  );
} 