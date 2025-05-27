"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { ThemeProvider } from "next-themes";
import { AnimatePresence } from "framer-motion";

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
  userId: "demo-user-123",
  isAuthenticated: false,
  isLoading: true,
});

// Custom hook to use the user context
export const useUser = () => useContext(UserContext);

// Provider component
export function Providers({ children }: { children: React.ReactNode }) {
  // Use localStorage-based authentication
  const [user, setUser] = useState<UserContextType>({
    userId: "demo-user-123",
    isAuthenticated: false,
    isLoading: true,
  });

  // Load user from localStorage and cookie
  useEffect(() => {
    const loadUser = async () => {
      try {
        // Check if we have a valid token
        const token = document.cookie
          .split("; ")
          .find((row) => row.startsWith("token="))
          ?.split("=")[1];

        if (token) {
          // Try to get user from localStorage
          const userData = localStorage.getItem("user");
          if (userData) {
            const parsedUser = JSON.parse(userData);
            setUser({
              userId: parsedUser.id,
              isAuthenticated: true,
              name: parsedUser.fullName,
              email: parsedUser.email,
              picture: `https://api.dicebear.com/7.x/micah/svg?seed=${parsedUser.fullName}`,
              isLoading: false,
            });
            return;
          }
        }

        // No valid authentication found
        setUser({
          userId: "demo-user-123",
          isAuthenticated: false,
          isLoading: false,
        });
      } catch (error) {
        console.error("Failed to load user:", error);
        setUser({
          userId: "demo-user-123",
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    loadUser();

    // Listen for storage events (when user logs in/out in another tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "user") {
        loadUser();
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <AnimatePresence mode="wait">
        <UserContext.Provider value={user}>{children}</UserContext.Provider>
      </AnimatePresence>
    </ThemeProvider>
  );
}
