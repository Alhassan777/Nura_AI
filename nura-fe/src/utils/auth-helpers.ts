export const handleAuthError = async (error: any) => {
  // Check if it's an authentication error
  if (
    error?.status === 401 ||
    error?.message?.includes("Auth session missing")
  ) {
    // Clear storage and redirect to login for any auth errors
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return true; // Indicates auth error was handled
  }

  return false; // Not an auth error
};

export const withAuthRetry = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 1
): Promise<T> => {
  let lastError: any;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;

      // If it's the last attempt, don't retry
      if (attempt === maxRetries) {
        break;
      }

      // Check if it's an auth error and handle it
      const authErrorHandled = await handleAuthError(error);

      // If auth error was handled by redirecting, don't continue
      if (authErrorHandled) {
        break;
      }

      // Wait a bit before retrying
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  throw lastError;
};
