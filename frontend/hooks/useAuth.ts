import { useState, useEffect } from "react";
import { useLocalStorage } from "usehooks-ts";
import { getCookie } from "cookies-next";

export interface User {
  id: string;
  email: string;
  fullName: string;
  phoneNumber: string;
  sub?: string; // For compatibility with existing voice code
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export function useAuth(): AuthState {
  const [user, setUser] = useLocalStorage<User | null>("user", null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated by verifying both localStorage and cookie
    const token = getCookie("token");

    if (token && user) {
      // User is authenticated - ensure compatibility with voice system
      const compatibleUser = {
        ...user,
        sub: user.id, // Add 'sub' field for Vapi compatibility
      };
      setUser(compatibleUser);
      setIsLoading(false);
    } else if (!token && user) {
      // Token expired but user still in localStorage - clear user
      setUser(null);
      setIsLoading(false);
    } else {
      // No token and no user - not authenticated
      setIsLoading(false);
    }
  }, [user, setUser]);

  return {
    user,
    isAuthenticated: !!user && !!getCookie("token"),
    isLoading,
  };
}

// Hook specifically for voice integration compatibility
export function useVoiceAuth() {
  const { user, isAuthenticated, isLoading } = useAuth();

  return {
    user: user
      ? {
          ...user,
          sub: user.id, // Ensure 'sub' field exists for Vapi
        }
      : null,
    isAuthenticated,
    isLoading,
  };
}
