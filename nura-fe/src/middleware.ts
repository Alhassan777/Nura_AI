import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session if expired - required for Server Components
  const { data: { user }, error } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl

  console.log("### MIDDLEWARE ###")
  console.log("Checking auth for path:", pathname)
  console.log("User authenticated:", !!user)

  // Define public routes that don't require authentication
  const publicRoutes = [
    '/login',
    '/signup',
    '/auth/confirm',
    '/verify-email',
    '/verify-confirmed',
    '/error',
    '/reset-password',
    '/forgot-password'
  ]

  // Check if the current path is a public route
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route))

  // If user is not authenticated and trying to access a protected route
  if (!user && !isPublicRoute) {
    console.log("Redirecting unauthenticated user to login")
    // Redirect to login page
    const loginUrl = new URL('/login', request.url)
    // Add the original URL as a redirect parameter
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // If user is authenticated and trying to access auth pages, redirect to home
  if (user && (pathname === '/login' || pathname === '/signup')) {
    console.log("Redirecting authenticated user away from auth pages")
    return NextResponse.redirect(new URL('/', request.url))
  }

  // For API routes, check authentication
  if (pathname.startsWith('/api/')) {
    // Skip auth check for public API routes
    const publicApiRoutes = [
      '/api/auth/',
      '/api/health'
    ]

    const isPublicApiRoute = publicApiRoutes.some(route => pathname.startsWith(route))

    if (!isPublicApiRoute && !user) {
      console.log("Blocking unauthenticated API request")
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }
  }

  console.log("Allowing request to proceed")
  return supabaseResponse
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
} 