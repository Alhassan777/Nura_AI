import { NextRequest, NextResponse } from "next/server";

const MEMORY_SERVICE_URL =
  process.env.MEMORY_SERVICE_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Check if this is a generic API proxy request
    if (body.endpoint) {
      const { endpoint, method = "POST", body: requestBody = {} } = body;

      const url = `${MEMORY_SERVICE_URL}${endpoint}`;
      const fetchOptions: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
        },
      };

      if (method !== "GET" && requestBody) {
        fetchOptions.body = JSON.stringify(requestBody);
      }

      const response = await fetch(url, fetchOptions);

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Unknown error" }));
        console.error(`Memory service error (${endpoint}):`, errorData);
        return NextResponse.json(
          {
            error: `Failed to ${method} ${endpoint}`,
            details: errorData,
          },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    }

    // Legacy chat endpoint support
    const { message, user_id, include_memory = true } = body;

    if (!message || !user_id) {
      return NextResponse.json(
        { error: "message and user_id are required" },
        { status: 400 }
      );
    }

    // Forward request to Python memory service
    const response = await fetch(
      `${MEMORY_SERVICE_URL}/chat/assistant?user_id=${user_id}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          include_memory,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Memory service error:", errorData);
      return NextResponse.json(
        {
          error: "Failed to get response from memory service",
          details: errorData,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    // Health check endpoint
    const response = await fetch(`${MEMORY_SERVICE_URL}/health`);
    const data = await response.json();

    return NextResponse.json({
      status: "ok",
      memory_service: data,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json(
      {
        status: "error",
        error: "Memory service unavailable",
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    );
  }
}
