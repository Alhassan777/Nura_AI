'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { useUser } from './providers';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { PhoneIcon, MessageSquareIcon } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { name, isLoading } = useUser();
  const [isCallDialogOpen, setIsCallDialogOpen] = useState(false);
  const [useBrowser, setUseBrowser] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isCallStarting, setIsCallStarting] = useState(false);

  // Handle starting a browser call
  const handleBrowserCall = () => {
    setIsCallStarting(true);
    // Simulate call connection
    setTimeout(() => {
      router.push('/call');
    }, 1500);
  };

  // Handle starting a phone call
  const handlePhoneCall = () => {
    if (!phoneNumber.trim()) return;
    
    setIsCallStarting(true);
    // Simulate call connection
    setTimeout(() => {
      // In a real app, this would initiate the call via an API
      alert(`Calling ${phoneNumber}... In a real app, this would connect to Vapi.ai`);
      setIsCallDialogOpen(false);
      setIsCallStarting(false);
    }, 1500);
  };

  // Handle starting a chat
  const handleStartChat = () => {
    router.push('/chat');
  };

  // Subtle glow animation for the welcome text
  const glowVariants = {
    animate: {
      textShadow: [
        "0 0 8px rgba(149, 128, 255, 0.5)",
        "0 0 16px rgba(149, 128, 255, 0.8)",
        "0 0 24px rgba(149, 128, 255, 0.3)",
        "0 0 8px rgba(149, 128, 255, 0.5)"
      ],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background flex items-center justify-center">
        <div className="w-16 h-16 border-t-4 border-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Animated smoke/fog effect */}
        <div className="absolute top-0 left-0 w-full h-full opacity-20">
          <motion.div 
            className="absolute top-1/4 left-1/3 w-96 h-96 rounded-full bg-purple-500/10 blur-3xl"
            animate={{
              x: [0, 30, -20, 0],
              y: [0, -30, 20, 0],
              scale: [1, 1.2, 0.9, 1],
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div 
            className="absolute bottom-1/4 right-1/3 w-96 h-96 rounded-full bg-blue-500/10 blur-3xl"
            animate={{
              x: [0, -40, 30, 0],
              y: [0, 40, -30, 0],
              scale: [1, 0.8, 1.1, 1],
            }}
            transition={{
              duration: 18,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1
            }}
          />
          <motion.div 
            className="absolute top-1/2 left-1/2 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl"
            animate={{
              x: [0, 50, -40, 0],
              y: [0, -50, 40, 0],
              scale: [1, 1.1, 0.9, 1],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
          />
        </div>
        
        {/* Enhanced grid effect */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080801a_1px,transparent_1px),linear-gradient(to_bottom,#8080801a_1px,transparent_1px)] bg-[size:30px_30px] opacity-30"></div>
      </div>
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="absolute inset-0 pointer-events-none overflow-hidden -z-10"
      >
        <div className="absolute -inset-[10px] opacity-10">
          {/* Neo grid background */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px]"></div>
          
          {/* Gradient orbs */}
          <div className="absolute top-0 left-0 -mt-40 -ml-40 w-96 h-96 bg-primary/20 dark:bg-primary/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 -mb-40 -mr-40 w-96 h-96 bg-slate-400/20 dark:bg-slate-900/20 rounded-full blur-3xl"></div>
        </div>
      </motion.div>
      
      <div className="container mx-auto px-4 py-16 max-w-4xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <motion.h1 
            className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400 dark:from-indigo-300 dark:to-purple-300"
            variants={glowVariants}
            animate="animate"
          >
            Welcome, {name?.split(' ')[0] || 'Friend'}
          </motion.h1>
          <p className="text-xl text-muted-foreground">
            How would you like to connect with Nura today?
          </p>
        </motion.div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            whileHover={{ y: -5 }}
            className="relative"
          >
            <Dialog open={isCallDialogOpen} onOpenChange={setIsCallDialogOpen}>
              <DialogTrigger asChild>
                <Button 
                  variant="outline" 
                  size="lg"
                  className="w-full h-60 rounded-xl border-2 bg-card/50 backdrop-blur-sm hover:bg-card/80 hover:border-primary/50 transition-all duration-300 flex flex-col items-center justify-center gap-4 shadow-[0_0_15px_rgba(79,70,229,0.15)]"
                >
                  <div className="relative">
                    <div className="absolute -inset-4 bg-primary/10 rounded-full animate-pulse"></div>
                    <PhoneIcon size={48} className="text-primary" />
                  </div>
                  <div className="text-lg font-semibold">Talk to Nura</div>
                  <p className="text-sm text-muted-foreground max-w-[80%] text-center px-4 whitespace-normal break-words leading-relaxed">
                    Have a conversation with Nura through voice for a more personal experience
                  </p>
                </Button>
              </DialogTrigger>
              
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Talk to Nura</DialogTitle>
                  <DialogDescription>
                    Choose how you'd like to start your conversation
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6 py-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="browser-call">Call through browser</Label>
                    <Switch 
                      id="browser-call"
                      checked={useBrowser}
                      onCheckedChange={setUseBrowser}
                    />
                  </div>
                  
                  <AnimatePresence mode="wait">
                    {useBrowser ? (
                      <motion.div
                        key="browser"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="text-center"
                      >
                        <p className="text-sm text-muted-foreground mb-4">
                          Start a voice call directly from your browser. Make sure your microphone is enabled.
                        </p>
                        <Button 
                          onClick={handleBrowserCall}
                          disabled={isCallStarting}
                          className="w-full"
                        >
                          {isCallStarting ? 'Connecting...' : 'Start Browser Call'}
                        </Button>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="phone"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="space-y-2">
                          <Label htmlFor="phone-number">Enter your phone number</Label>
                          <Input 
                            id="phone-number"
                            placeholder="+1 (555) 123-4567"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                          />
                          <p className="text-xs text-muted-foreground">
                            Standard rates may apply. Nura will call you at this number.
                          </p>
                        </div>
                        <Button 
                          onClick={handlePhoneCall}
                          disabled={!phoneNumber.trim() || isCallStarting}
                          className="w-full mt-4"
                        >
                          {isCallStarting ? 'Connecting...' : 'Call My Phone'}
                        </Button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </DialogContent>
            </Dialog>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            whileHover={{ y: -5 }}
          >
            <Button 
              variant="outline"
              size="lg"
              className="w-full h-60 rounded-xl border-2 bg-card/50 backdrop-blur-sm hover:bg-card/80 hover:border-primary/50 transition-all duration-300 flex flex-col items-center justify-center gap-4 shadow-[0_0_15px_rgba(79,70,229,0.15)]"
              onClick={handleStartChat}
            >
              <div className="relative">
                <div className="absolute -inset-4 bg-primary/10 rounded-full"></div>
                <MessageSquareIcon size={48} className="text-primary" />
              </div>
              <div className="text-lg font-semibold">Chat with Nura</div>
              <p className="text-sm text-muted-foreground max-w-[80%] text-center px-4 whitespace-normal break-words leading-relaxed">
                Send messages and photos to Nura for a text-based conversation
              </p>
            </Button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
