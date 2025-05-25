import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// This is a simplified middleware that doesn't rely on Auth0 edge
// It will be replaced by Auth0's session check in the actual components
export function middleware(req: NextRequest) {
  // In a real implementation with Auth0, we would check for session here
  // Instead, we'll just keep the middleware simple and let client components handle auth
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Only apply to dashboard routes and home
    '/dashboard/:path*',
    '/'
  ],
}; 