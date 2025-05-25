import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/chat/assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: "Failed to process chat request" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);

    if (!response.ok) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json({
      status: "healthy",
      backend: data,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json(
      {
        status: "unhealthy",
        error: "Backend service unavailable",
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    );
  }
}
