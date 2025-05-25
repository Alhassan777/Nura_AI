'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeProvider } from 'next-themes';
import { AnimatePresence } from 'framer-motion';

// Create a context for the user
interface UserContextType {
  userId: string;
  isAuthenticated: boolean;
  name?: string;
  email?: string;
  picture?: string;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType>({
  userId: 'demo-user-123',
  isAuthenticated: false,
  isLoading: true
});

// Custom hook to use the user context
export const useUser = () => useContext(UserContext);

// Provider component
export function Providers({ children }: { children: React.ReactNode }) {
  // For demo purposes, we're using a static user
  // In a real implementation, this would fetch the user from Auth0
  const [user, setUser] = useState<UserContextType>({
    userId: 'demo-user-123',
    isAuthenticated: true,
    name: 'Demo User',
    email: 'demo@example.com',
    picture: 'https://api.dicebear.com/7.x/micah/svg?seed=Demo',
    isLoading: false
  });

  // In a real implementation, this would fetch the user session from Auth0
  useEffect(() => {
    // Simulate loading the user
    const loadUser = async () => {
      try {
        // In real implementation, fetch from /api/auth/me
        // Mock user loading for demo
        setTimeout(() => {
          setUser({
            userId: 'demo-user-123',
            isAuthenticated: true,
            name: 'Demo User',
            email: 'demo@example.com',
            picture: 'https://api.dicebear.com/7.x/micah/svg?seed=Demo',
            isLoading: false
          });
        }, 500);
      } catch (error) {
        console.error('Failed to load user:', error);
        setUser({
          userId: 'demo-user-123',
          isAuthenticated: false,
          isLoading: false
        });
      }
    };

    loadUser();
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <AnimatePresence mode="wait">
        <UserContext.Provider value={user}>
          {children}
        </UserContext.Provider>
      </AnimatePresence>
    </ThemeProvider>
  );
} 