'use client';

import React, { useState } from 'react';
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background flex items-center justify-center">
        <div className="w-16 h-16 border-t-4 border-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/90 dark:from-card dark:to-background">
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
      
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
            Welcome, {name?.split(' ')[0] || 'Friend'}
          </h1>
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
                  className="w-full h-60 rounded-xl border-2 bg-card/50 backdrop-blur-sm hover:bg-card/80 hover:border-primary/50 transition-all duration-300 flex flex-col items-center justify-center gap-4"
                >
                  <div className="relative">
                    <div className="absolute -inset-4 bg-primary/10 rounded-full animate-pulse"></div>
                    <PhoneIcon size={48} className="text-primary" />
                  </div>
                  <div className="text-lg font-semibold">Talk to Nura</div>
                  <p className="text-sm text-muted-foreground max-w-xs">
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
              className="w-full h-60 rounded-xl border-2 bg-card/50 backdrop-blur-sm hover:bg-card/80 hover:border-primary/50 transition-all duration-300 flex flex-col items-center justify-center gap-4"
              onClick={handleStartChat}
            >
              <div className="relative">
                <div className="absolute -inset-4 bg-primary/10 rounded-full"></div>
                <MessageSquareIcon size={48} className="text-primary" />
              </div>
              <div className="text-lg font-semibold">Chat with Nura</div>
              <p className="text-sm text-muted-foreground max-w-xs">
                Send messages and photos to Nura for a text-based conversation
              </p>
            </Button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
