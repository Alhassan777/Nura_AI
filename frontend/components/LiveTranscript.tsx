'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { 
  Mic, 
  Bot, 
  Volume2, 
  VolumeX, 
  Download, 
  Copy, 
  Eye, 
  EyeOff,
  Clock,
  MessageSquare
} from 'lucide-react';
import { toast } from 'sonner';

interface TranscriptMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  duration?: number;
}

interface LiveTranscriptProps {
  isCallActive: boolean;
  messages: TranscriptMessage[];
  onToggleVisibility?: () => void;
  showTimestamps?: boolean;
  showConfidence?: boolean;
  className?: string;
  maxHeight?: string;
}

const LiveTranscript: React.FC<LiveTranscriptProps> = ({
  isCallActive,
  messages,
  onToggleVisibility,
  showTimestamps = true,
  showConfidence = false,
  className = '',
  maxHeight = '400px',
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [currentSpeaker, setCurrentSpeaker] = useState<'user' | 'assistant' | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Detect current speaker based on recent activity
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      const now = new Date();
      const timeDiff = now.getTime() - lastMessage.timestamp.getTime();
      
      // Consider someone "currently speaking" if their last message was within 3 seconds
      if (timeDiff < 3000) {
        setCurrentSpeaker(lastMessage.role);
      } else {
        setCurrentSpeaker(null);
      }
    }
  }, [messages]);

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
    onToggleVisibility?.();
  };

  const copyTranscript = async () => {
    try {
      const transcriptText = messages
        .map(msg => {
          const timestamp = showTimestamps 
            ? `[${msg.timestamp.toLocaleTimeString()}] ` 
            : '';
          const role = msg.role === 'user' ? 'You' : 'Assistant';
          return `${timestamp}${role}: ${msg.content}`;
        })
        .join('\n');

      await navigator.clipboard.writeText(transcriptText);
      toast.success('Transcript copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy transcript');
    }
  };

  const downloadTranscript = () => {
    try {
      const transcriptText = messages
        .map(msg => {
          const timestamp = `[${msg.timestamp.toLocaleString()}]`;
          const role = msg.role === 'user' ? 'You' : 'Assistant';
          const confidence = msg.confidence 
            ? ` (${(msg.confidence * 100).toFixed(0)}% confidence)` 
            : '';
          return `${timestamp} ${role}${confidence}: ${msg.content}`;
        })
        .join('\n\n');

      const blob = new Blob([transcriptText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `voice-transcript-${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Transcript downloaded');
    } catch (error) {
      toast.error('Failed to download transcript');
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getTotalDuration = () => {
    if (messages.length === 0) return 0;
    const start = messages[0].timestamp;
    const end = messages[messages.length - 1].timestamp;
    return Math.round((end.getTime() - start.getTime()) / 1000);
  };

  const getMessageStats = () => {
    const userMessages = messages.filter(m => m.role === 'user').length;
    const assistantMessages = messages.filter(m => m.role === 'assistant').length;
    return { userMessages, assistantMessages, total: messages.length };
  };

  if (!isVisible) {
    return (
      <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
        <Button
          onClick={toggleVisibility}
          variant="outline"
          size="sm"
          className="rounded-full shadow-lg"
        >
          <MessageSquare className="h-4 w-4 mr-2" />
          Show Transcript
        </Button>
      </div>
    );
  }

  const stats = getMessageStats();

  return (
    <Card className={`w-full ${className}`} style={{ maxHeight }}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Live Transcript
            {isCallActive && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                <span className="ml-2 px-2 py-1 text-xs rounded-md border border-green-500 text-green-600 dark:text-green-400 flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                  Live
                </span>
              </motion.div>
            )}
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Current speaker indicator */}
            {currentSpeaker && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-1"
              >
                {currentSpeaker === 'user' ? (
                  <Mic className="h-4 w-4 text-blue-500" />
                ) : (
                  <Bot className="h-4 w-4 text-purple-500" />
                )}
                <span className="text-xs text-muted-foreground">
                  {currentSpeaker === 'user' ? 'You' : 'Assistant'}
                </span>
              </motion.div>
            )}

            {/* Action buttons */}
            <Button
              variant="ghost"
              size="sm"
              onClick={copyTranscript}
              disabled={messages.length === 0}
              className="h-8 w-8 p-0"
            >
              <Copy className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={downloadTranscript}
              disabled={messages.length === 0}
              className="h-8 w-8 p-0"
            >
              <Download className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={toggleVisibility}
              className="h-8 w-8 p-0"
            >
              <EyeOff className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Stats row */}
        {messages.length > 0 && (
          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {getTotalDuration()}s
            </div>
            <div>{stats.total} messages</div>
            <div className="flex items-center gap-1">
              <Mic className="h-3 w-3" />
              {stats.userMessages}
            </div>
            <div className="flex items-center gap-1">
              <Bot className="h-3 w-3" />
              {stats.assistantMessages}
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        <div 
          className="h-full w-full overflow-y-auto" 
          ref={scrollAreaRef}
          style={{ maxHeight: `calc(${maxHeight} - 120px)` }}
        >
          <div className="space-y-3 pr-4">
            <AnimatePresence initial={false}>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.95 }}
                  transition={{ duration: 0.3 }}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {/* Avatar for assistant messages */}
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    </div>
                  )}

                  {/* Message content */}
                  <div className={`
                    flex flex-col gap-1 max-w-[80%]
                    ${message.role === 'user' ? 'items-end' : 'items-start'}
                  `}>
                    <div className={`
                      rounded-lg px-3 py-2 text-sm
                      ${message.role === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted'
                      }
                    `}>
                      {message.content}
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {showTimestamps && (
                        <span>{formatTimestamp(message.timestamp)}</span>
                      )}
                      
                      {showConfidence && message.confidence && (
                        <span className={getConfidenceColor(message.confidence)}>
                          {(message.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                      
                      {message.duration && (
                        <span>{message.duration}s</span>
                      )}
                    </div>
                  </div>

                  {/* Avatar for user messages */}
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                      <Mic className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Empty state */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <motion.div
                  animate={{ 
                    scale: isCallActive ? [1, 1.1, 1] : 1,
                    opacity: isCallActive ? [0.5, 1, 0.5] : 0.5 
                  }}
                  transition={{ 
                    duration: 2, 
                    repeat: isCallActive ? Infinity : 0 
                  }}
                >
                  <MessageSquare className="h-12 w-12 text-muted-foreground mb-3" />
                </motion.div>
                <p className="text-muted-foreground">
                  {isCallActive 
                    ? 'Waiting for conversation to begin...'
                    : 'Start a voice call to see the transcript here'
                  }
                </p>
              </div>
            )}

            {/* Auto-scroll anchor */}
            <div ref={endOfMessagesRef} />
          </div>
        </div>

        {/* Auto-scroll toggle */}
        {messages.length > 3 && (
          <div className="flex justify-center pt-3 border-t">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
              className="text-xs"
            >
              {autoScroll ? (
                <>
                  <VolumeX className="h-3 w-3 mr-1" />
                  Auto-scroll ON
                </>
              ) : (
                <>
                  <Volume2 className="h-3 w-3 mr-1" />
                  Auto-scroll OFF
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LiveTranscript; 