import { cookies } from "next/headers";

export interface AuthenticatedUser {
  id: string;
  email: string;
  fullName: string;
  phoneNumber: string;
}

/**
 * Extract user information from authentication context
 * This is a simplified implementation for the current localStorage-based auth system
 * In a real implementation, this would decode JWT tokens or query a session store
 */
export async function getAuthenticatedUser(): Promise<AuthenticatedUser | null> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("token")?.value;

    if (!token) {
      return null;
    }

    // For the current localStorage-based system, we'll use a simple approach
    // In a real implementation, you would decode the JWT or query the session
    // For now, we'll return a consistent user structure
    return {
      id: "1", // This should match the ID set in LoginForm/SignupForm
      email: "demo@example.com",
      fullName: "John Doe",
      phoneNumber: "1234567890",
    };
  } catch (error) {
    console.error("Failed to get authenticated user:", error);
    return null;
  }
}

/**
 * Check if a request is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("token")?.value;
    return !!token;
  } catch (error) {
    console.error("Failed to check authentication:", error);
    return false;
  }
}

/**
 * Get customer ID for voice integration
 * Uses the user's ID as the customer ID for Vapi calls
 */
export async function getCustomerIdForVoice(): Promise<string | null> {
  const user = await getAuthenticatedUser();
  return user ? user.id : null;
}
