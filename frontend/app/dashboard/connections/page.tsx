'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useUser } from '@/app/providers';
import { useRouter } from 'next/navigation';

// Mock data for connections
interface Connection {
  id: string;
  name: string;
  email: string;
  avatar: string;
  status: 'active' | 'inactive' | 'pending';
  lastActive?: string;
}

const mockConnections: Connection[] = [
  {
    id: '1',
    name: 'Emma Thompson',
    email: 'emma.t@example.com',
    avatar: 'https://api.dicebear.com/7.x/micah/svg?seed=Emma',
    status: 'active',
    lastActive: '2 hours ago'
  },
  {
    id: '2',
    name: 'James Wilson',
    email: 'james.w@example.com',
    avatar: 'https://api.dicebear.com/7.x/micah/svg?seed=James',
    status: 'active',
    lastActive: '1 day ago'
  },
  {
    id: '3',
    name: 'Sophia Martinez',
    email: 'sophia.m@example.com',
    avatar: 'https://api.dicebear.com/7.x/micah/svg?seed=Sophia',
    status: 'inactive',
    lastActive: '5 days ago'
  },
  {
    id: '4',
    name: 'David Lee',
    email: 'david.l@example.com',
    avatar: 'https://api.dicebear.com/7.x/micah/svg?seed=David',
    status: 'pending'
  }
];

export default function ConnectionsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useUser();
  const [connections] = useState<Connection[]>(mockConnections);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  // Redirect to auth page if not authenticated
  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, isLoading, router]);

  // Don't render the page until we know the auth state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-t-2 border-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inviteEmail) return;
    
    setIsInviting(true);
    
    // Simulate sending invite
    setTimeout(() => {
      setIsInviting(false);
      setShowSuccess(true);
      setInviteEmail('');
      
      // Hide success message after a few seconds
      setTimeout(() => {
        setShowSuccess(false);
      }, 3000);
    }, 1500);
  };

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
            Your Support Network
          </h1>
          <p className="text-muted-foreground">Connect with friends and family for mutual support</p>
        </motion.div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div 
            className="lg:col-span-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="backdrop-blur-sm bg-background/60 dark:bg-card/60 border-neutral-200/20 dark:border-neutral-800/50">
              <CardHeader>
                <CardTitle>Your Connections</CardTitle>
                <CardDescription>
                  People in your support network
                </CardDescription>
              </CardHeader>
              <CardContent>
                {connections.length > 0 ? (
                  <ul className="space-y-4">
                    {connections.map((connection) => (
                      <li key={connection.id} className="flex items-center justify-between p-3 rounded-lg bg-background/80 dark:bg-card/80 border border-neutral-200/10 dark:border-neutral-800/30">
                        <div className="flex items-center">
                          <div className="w-10 h-10 rounded-full overflow-hidden bg-primary/10 flex-shrink-0">
                            <img 
                              src={connection.avatar} 
                              alt={connection.name} 
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="ml-3">
                            <h3 className="font-medium">{connection.name}</h3>
                            <p className="text-xs text-muted-foreground">{connection.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center">
                          {connection.status === 'pending' ? (
                            <span className="text-xs px-2 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
                              Pending
                            </span>
                          ) : (
                            <div className="flex flex-col items-end">
                              <span className={`inline-block w-2 h-2 rounded-full ${connection.status === 'active' ? 'bg-green-500' : 'bg-neutral-400'}`}></span>
                              <span className="text-xs text-muted-foreground mt-1">
                                {connection.lastActive}
                              </span>
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-10">
                    <p className="text-muted-foreground">You haven't connected with anyone yet.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="backdrop-blur-sm bg-background/60 dark:bg-card/60 border-neutral-200/20 dark:border-neutral-800/50">
              <CardHeader>
                <CardTitle>Invite Someone</CardTitle>
                <CardDescription>
                  Add a friend or family member to your support network
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleInvite} className="space-y-4">
                  <div>
                    <label htmlFor="email" className="text-sm font-medium block mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="friend@example.com"
                      className="w-full p-2 rounded-md border border-neutral-200/30 dark:border-neutral-800/50 bg-background dark:bg-card focus:outline-none focus:ring-1 focus:ring-primary"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="message" className="text-sm font-medium block mb-1">
                      Personal Message (Optional)
                    </label>
                    <textarea
                      id="message"
                      placeholder="I'd like to add you to my Nura support network..."
                      className="w-full h-20 p-2 rounded-md border border-neutral-200/30 dark:border-neutral-800/50 bg-background dark:bg-card focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  
                  <Button 
                    type="submit"
                    className="w-full"
                    disabled={isInviting || !inviteEmail}
                  >
                    {isInviting ? 'Sending Invite...' : 'Send Invitation'}
                  </Button>
                  
                  {showSuccess && (
                    <motion.p 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="text-sm text-green-600 dark:text-green-400 text-center mt-2"
                    >
                      Invitation sent successfully!
                    </motion.p>
                  )}
                </form>
              </CardContent>
              <CardFooter>
                <p className="text-xs text-muted-foreground">
                  When someone accepts your invitation, they'll appear in your connections list.
                </p>
              </CardFooter>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
} 