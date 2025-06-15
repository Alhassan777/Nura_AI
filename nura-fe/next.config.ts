import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: false,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "ik.imagekit.io",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/safety-invitations/:path*",
        destination: "http://localhost:8000/safety-invitations/:path*",
      },
      {
        source: "/safety-network/:path*",
        destination: "http://localhost:8000/safety-network/:path*",
      },
      {
        source: "/memory/:path*",
        destination: "http://localhost:8000/memory/:path*",
      },
      {
        source: "/chat/:path*",
        destination: "http://localhost:8000/chat/:path*",
      },
      {
        source: "/privacy/:path*",
        destination: "http://localhost:8000/privacy/:path*",
      },
      {
        source: "/assistant/:path*",
        destination: "http://localhost:8000/assistant/:path*",
      },
      {
        source: "/audit/:path*",
        destination: "http://localhost:8000/audit/:path*",
      },
      {
        source: "/voice/:path*",
        destination: "http://localhost:8000/voice/:path*",
      },
      {
        source: "/scheduling/:path*",
        destination: "http://localhost:8000/scheduling/:path*",
      },
      {
        source: "/users/:path*",
        destination: "http://localhost:8000/users/:path*",
      },
      {
        source: "/auth/:path*",
        destination: "http://localhost:8000/auth/:path*",
      },
      {
        source: "/image-generation/:path*",
        destination: "http://localhost:8000/image-generation/:path*",
      },
    ];
  },
};

export default nextConfig;
