'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SendIcon, ImageIcon, HomeIcon, Loader2Icon } from 'lucide-react';
import { format } from 'date-fns';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useUser } from '../providers';

// Message types
type MessageType = 'text' | 'image';

interface Message {
  id: string;
  content: string;
  type: MessageType;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatPage() {
  const router = useRouter();
  const { name, picture } = useUser();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hi there! I'm Nura, your mental health assistant. How are you feeling today?",
      type: 'text',
      sender: 'assistant',
      timestamp: new Date(Date.now() - 60000) // 1 minute ago
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Auto scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // Handle sending a message
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Add user message
    const userMessageId = Date.now().toString();
    const userMessage: Message = {
      id: userMessageId,
      content: inputValue,
      type: 'text',
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // Simulate AI processing delay
    setTimeout(() => {
      simulateResponse(userMessage.content);
    }, 1500);
  };
  
  // Simulate responses based on user input (in a real app, this would call an API)
  const simulateResponse = (userInput: string) => {
    let response = "I'm here to listen. Can you tell me more about that?";
    
    const lowerInput = userInput.toLowerCase();
    
    if (lowerInput.includes('sad') || lowerInput.includes('depressed') || lowerInput.includes('unhappy')) {
      response = "I'm sorry to hear you're feeling down. Remember that it's okay to not be okay sometimes. Would you like to explore some coping strategies that might help?";
    } 
    else if (lowerInput.includes('anxious') || lowerInput.includes('worried') || lowerInput.includes('stress')) {
      response = "Feeling anxious can be really challenging. Have you tried any breathing exercises? Taking slow, deep breaths for a few minutes can help calm your nervous system.";
    }
    else if (lowerInput.includes('happy') || lowerInput.includes('good') || lowerInput.includes('great')) {
      response = "I'm glad to hear you're doing well! Celebrating these positive moments is important. What's contributing to your good mood today?";
    }
    else if (lowerInput.includes('tired') || lowerInput.includes('exhausted') || lowerInput.includes('sleep')) {
      response = "Rest is so important for mental health. Have you been able to maintain a regular sleep schedule? Even small improvements in sleep habits can make a big difference.";
    }
    else if (lowerInput.includes('hello') || lowerInput.includes('hi') || lowerInput.includes('hey')) {
      response = `Hello! It's nice to connect with you today. How are you feeling?`;
    }
    
    // Add assistant response
    setTimeout(() => {
      setMessages(prev => [
        ...prev, 
        {
          id: (Date.now() + 1).toString(),
          content: response,
          type: 'text',
          sender: 'assistant',
          timestamp: new Date()
        }
      ]);
      setIsLoading(false);
    }, 500);
  };
  
  // Handle image upload
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Create a file reader to read the image
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        // Add user image message
        const imageMessage: Message = {
          id: Date.now().toString(),
          content: event.target.result as string,
          type: 'image',
          sender: 'user',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, imageMessage]);
        setIsLoading(true);
        
        // Simulate AI response to image
        setTimeout(() => {
          setMessages(prev => [
            ...prev, 
            {
              id: (Date.now() + 1).toString(),
              content: "Thank you for sharing this image with me. What emotions does this picture bring up for you?",
              type: 'text',
              sender: 'assistant',
              timestamp: new Date()
            }
          ]);
          setIsLoading(false);
        }, 2000);
      }
    };
    
    reader.readAsDataURL(file);
    
    // Reset the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background flex flex-col">
      {/* Chat header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-background/80 dark:bg-card/80 backdrop-blur-md border-b border-neutral-200/20 dark:border-neutral-800/50 py-4 px-4 flex items-center justify-between sticky top-0 z-10"
      >
        <div className="flex items-center">
          <Avatar className="h-10 w-10 mr-3">
            <AvatarImage src="/nura-avatar.png" alt="Nura" />
            <AvatarFallback className="bg-primary/10 text-primary">N</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="font-semibold text-primary">Nura</h1>
            <p className="text-xs text-muted-foreground">Mental Health Assistant</p>
          </div>
        </div>
        
        <Button 
          variant="ghost" 
          size="icon"
          onClick={() => router.push('/')}
          className="rounded-full"
        >
          <HomeIcon size={20} />
        </Button>
      </motion.div>
      
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] ${
                  message.sender === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-card dark:bg-card/80 border border-neutral-200/20 dark:border-neutral-800/50'
                } rounded-2xl px-4 py-3 shadow-sm`}
              >
                {message.type === 'text' ? (
                  <p className="whitespace-pre-line">{message.content}</p>
                ) : (
                  <img 
                    src={message.content} 
                    alt="User uploaded" 
                    className="max-w-full rounded-lg max-h-60 object-contain"
                  />
                )}
                <p className={`text-xs mt-1 ${
                  message.sender === 'user' 
                    ? 'text-primary-foreground/70' 
                    : 'text-muted-foreground'
                }`}>
                  {format(message.timestamp, 'h:mm a')}
                </p>
              </div>
            </motion.div>
          ))}
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="max-w-[80%] bg-card dark:bg-card/80 border border-neutral-200/20 dark:border-neutral-800/50 rounded-2xl px-4 py-3 shadow-sm flex items-center">
                <div className="flex space-x-2 items-center text-muted-foreground">
                  <Loader2Icon size={16} className="animate-spin" />
                  <span>Nura is typing...</span>
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </AnimatePresence>
      </div>
      
      {/* Chat input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-background/80 dark:bg-card/80 backdrop-blur-md border-t border-neutral-200/20 dark:border-neutral-800/50 p-4"
      >
        <form 
          onSubmit={handleSendMessage}
          className="flex items-center space-x-2"
        >
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="rounded-full shrink-0"
            onClick={() => fileInputRef.current?.click()}
          >
            <ImageIcon size={20} className="text-muted-foreground" />
          </Button>
          
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Message Nura..."
            className="flex-1 bg-background/50 dark:bg-card/50 border-neutral-200/30 dark:border-neutral-800/30 focus-visible:ring-primary"
            disabled={isLoading}
          />
          
          <Button
            type="submit"
            size="icon"
            className="rounded-full shrink-0"
            disabled={!inputValue.trim() || isLoading}
          >
            <SendIcon size={18} />
          </Button>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            className="hidden"
            disabled={isLoading}
          />
        </form>
      </motion.div>
    </div>
  );
} 