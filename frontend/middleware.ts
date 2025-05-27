import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Simplified middleware for localStorage-based authentication
// The actual authentication checks are handled in components
export function middleware(req: NextRequest) {
  // Keep the middleware simple and let client components handle auth
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Only apply to dashboard routes and home
    "/dashboard/:path*",
    "/",
  ],
};
