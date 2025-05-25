import { handleAuth } from '@auth0/nextjs-auth0';

// Export the handlers using Next.js App Router pattern for API routes
export const GET = handleAuth();
export const POST = handleAuth(); 