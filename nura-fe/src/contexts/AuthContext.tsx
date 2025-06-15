"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { getCurrentUser, logout as logoutAction } from "@/utils/login-actions";
import { useRouter } from "next/navigation";
import { createClient } from "@/utils/supabase/client";

interface User {
  id: string;
  email: string;
  phone_number?: string | null;
  full_name?: string | null;
  display_name?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  is_verified: boolean;
  current_streak: number;
  xp: number;
  privacy_settings: object;
  created_at?: string | null;
  updated_at?: string | null;
  last_active_at?: string | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
  isAuthenticated: boolean;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const { push } = useRouter();

  const setUser = (userData: User | null) => {
    setUserState(userData);
    if (userData && typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(userData));
    } else if (typeof window !== "undefined") {
      localStorage.removeItem("user");
    }
  };

  const refreshUser = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const userData = await getCurrentUser();
      if (userData) {
        setUser(userData);
      } else {
        setUser(null);
        // Clear invalid tokens
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user");
        }
      }
    } catch (e: any) {
      console.error("Error fetching user:", e);
      setError(e);
      setUser(null);
      // Clear invalid tokens
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const supabaeLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
  };

  const logout = async () => {
    try {
      await supabaeLogout();
      await logoutAction();
      setUser(null);
      setError(null);
      push("/login");
    } catch (e: any) {
      console.error("Error during logout:", e);
      // Clear local state even if logout fails
      setUser(null);
    }
  };

  useEffect(() => {
    // Check for existing auth token on mount
    const checkAuthStatus = async () => {
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("auth_token");
        const localUser = localStorage.getItem("user");

        if (token) {
          try {
            // Try to get fresh user data from backend
            await refreshUser();
          } catch (error) {
            // If refresh fails, clear everything and redirect
            localStorage.removeItem("auth_token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user");
            await supabaeLogout();
            setIsLoading(false);
            push("/login");
          }
        } else if (localUser) {
          try {
            // Parse and set local user data, but still verify with backend
            const parsedUser = JSON.parse(localUser);
            setUserState(parsedUser);
            setIsLoading(false);
            // Verify in background
            setTimeout(async () => {
              try {
                await refreshUser();
              } catch (error) {
                // If verification fails, clear everything and redirect
                localStorage.removeItem("auth_token");
                localStorage.removeItem("refresh_token");
                localStorage.removeItem("user");
                await supabaeLogout();
                setUserState(null);
                push("/login");
              }
            }, 100);
          } catch {
            // Invalid local data, clear it and redirect
            localStorage.removeItem("user");
            await supabaeLogout();
            setIsLoading(false);
            push("/login");
          }
        } else {
          // No token or local user data, redirect to login
          setIsLoading(false);
          push("/login");
        }
      } else {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const value = {
    user,
    isLoading,
    error,
    isAuthenticated: !!user,
    logout,
    refreshUser,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
