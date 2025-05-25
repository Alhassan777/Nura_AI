'use client';

import React, { useEffect, useState } from 'react';
import { ClientStorageService, CallData } from '@/services/storageService';
import Link from 'next/link';
import { useUser } from '../providers';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const router = useRouter();
  const { userId, isAuthenticated, isLoading, name } = useUser();
  const [calls, setCalls] = useState<CallData[]>([]);
  const [loading, setLoading] = useState(true);

  // Redirect to auth page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    // Load calls on component mount if authenticated
    if (isAuthenticated && !isLoading) {
      const userCalls = ClientStorageService.getCalls(userId);
      setCalls(userCalls);
      setLoading(false);
    }
  }, [userId, isAuthenticated, isLoading]);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  // Don't render the dashboard until we know the auth state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-t-2 border-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // Don't render the dashboard if not authenticated
  if (!isAuthenticated) {
    return null;
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
      
      <div className="container mx-auto px-4 py-12">
        <motion.div 
          className="mb-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80 mb-2">
            Welcome, {name || 'Friend'}
          </h1>
          <p className="text-muted-foreground">Here's your mental health journey with Nura</p>
        </motion.div>
        
        <motion.div 
          className="flex justify-between items-center mb-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <h2 className="text-2xl font-semibold">
            Your Call History
          </h2>
          <div className="flex space-x-3">
            <Button 
              variant="outline" 
              asChild
              className="border-neutral-200/30 dark:border-neutral-800/50"
            >
              <Link href="/dashboard/import-demo">
                Import Demo Data
              </Link>
            </Button>
            <Button asChild>
              <Link href="/">
                Start New Call
              </Link>
            </Button>
          </div>
        </motion.div>
        
        {loading ? (
          <motion.div 
            className="flex justify-center py-20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 border-t-2 border-l-2 border-primary rounded-full animate-spin mb-4"></div>
              <p className="text-muted-foreground">Loading your calls...</p>
            </div>
          </motion.div>
        ) : calls.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="backdrop-blur-sm bg-background/60 dark:bg-card/60 border-neutral-200/20 dark:border-neutral-800/50">
              <CardContent className="p-10 text-center">
                <div className="mb-6 opacity-60">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold mb-2">No calls yet</h2>
                <p className="mb-6 text-muted-foreground">You haven't made any calls with Nura yet.</p>
                <div className="flex justify-center space-x-4">
                  <Button variant="outline" asChild className="border-neutral-200/30 dark:border-neutral-800/50">
                    <Link href="/dashboard/import-demo">
                      Import Demo Data
                    </Link>
                  </Button>
                  <Button asChild>
                    <Link href="/">
                      Start a New Call
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            variants={container}
            initial="hidden"
            animate="show"
          >
            {calls.map((call) => (
              <motion.div key={call.id} variants={item}>
                <Link href={`/dashboard/call/${call.id}`} className="block">
                  <Card className="h-full backdrop-blur-sm bg-background/60 dark:bg-card/60 border-neutral-200/20 dark:border-neutral-800/50 overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                    <CardHeader className="pb-2 bg-gradient-to-r from-background/60 to-background/60 via-primary/5 dark:from-card/60 dark:to-card/60 dark:via-primary/10">
                      <CardTitle className="text-lg">
                        {call.emotionalData?.scene_title || 'Call'}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {new Date(call.date).toLocaleString()}
                      </p>
                    </CardHeader>
                    <CardContent>
                      <p className="line-clamp-3 text-sm text-muted-foreground">
                        {call.summary?.substring(0, 100)}...
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
} 