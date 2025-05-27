import { NextRequest, NextResponse } from "next/server";
import { getCustomerIdForVoice, isAuthenticated } from "@/utils/auth-helpers";

interface VoiceStartRequest {
  mode: "web" | "phone";
  phoneNumber?: string; // Required for phone mode
  customerId?: string; // User identifier
}

const VAPI_API_KEY = process.env.VAPI_API_KEY;
const VAPI_DEFAULT_ASSISTANT_ID =
  process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID;
const MEMORY_SERVICE_URL =
  process.env.MEMORY_SERVICE_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    // Check authentication
    if (!(await isAuthenticated())) {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const mode = searchParams.get("mode") as "web" | "phone";
    const phoneNumber = searchParams.get("phoneNumber");

    // Get the authenticated user's ID for voice integration
    const authenticatedCustomerId = await getCustomerIdForVoice();
    const customerId =
      searchParams.get("customerId") ||
      authenticatedCustomerId ||
      "demo-user-123";

    if (!mode || !["web", "phone"].includes(mode)) {
      return NextResponse.json(
        { error: "Invalid mode. Must be 'web' or 'phone'" },
        { status: 400 }
      );
    }

    if (mode === "phone" && !phoneNumber) {
      return NextResponse.json(
        { error: "Phone number is required for phone mode" },
        { status: 400 }
      );
    }

    if (!VAPI_API_KEY || !VAPI_DEFAULT_ASSISTANT_ID) {
      return NextResponse.json(
        { error: "Vapi configuration missing" },
        { status: 500 }
      );
    }

    if (mode === "web") {
      // Return payload for frontend web SDK
      const startPayload = {
        assistantId: VAPI_DEFAULT_ASSISTANT_ID,
        customerId: customerId,
        metadata: {
          customerId: customerId,
          mode: "web",
          timestamp: new Date().toISOString(),
        },
      };

      return NextResponse.json({
        mode: "web",
        startPayload,
        success: true,
      });
    } else {
      // Phone mode - trigger server-side call
      const callResponse = await fetch("https://api.vapi.ai/call/phone", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${VAPI_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          assistantId: VAPI_DEFAULT_ASSISTANT_ID,
          customer: {
            number: phoneNumber,
          },
          metadata: {
            customerId: customerId,
            mode: "phone",
            timestamp: new Date().toISOString(),
          },
        }),
      });

      if (!callResponse.ok) {
        const errorData = await callResponse.json().catch(() => ({}));
        return NextResponse.json(
          {
            error: "Failed to initiate phone call",
            details: errorData,
          },
          { status: callResponse.status }
        );
      }

      const callData = await callResponse.json();

      // Store callId -> customerId mapping in our backend
      try {
        await fetch(`${MEMORY_SERVICE_URL}/voice/mapping`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            callId: callData.id,
            customerId: customerId,
            mode: "phone",
            phoneNumber: phoneNumber,
          }),
        });
      } catch (mappingError) {
        console.error("Failed to store call mapping:", mappingError);
        // Continue anyway - the call was initiated successfully
      }

      return NextResponse.json({
        mode: "phone",
        callId: callData.id,
        status: callData.status,
        success: true,
      });
    }
  } catch (error) {
    console.error("Voice start error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    if (!(await isAuthenticated())) {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const body: VoiceStartRequest = await request.json();
    const { mode, phoneNumber } = body;

    // Get the authenticated user's ID for voice integration
    const authenticatedCustomerId = await getCustomerIdForVoice();
    const customerId =
      body.customerId || authenticatedCustomerId || "demo-user-123";

    if (!mode || !["web", "phone"].includes(mode)) {
      return NextResponse.json(
        { error: "Invalid mode. Must be 'web' or 'phone'" },
        { status: 400 }
      );
    }

    if (mode === "phone" && !phoneNumber) {
      return NextResponse.json(
        { error: "Phone number is required for phone mode" },
        { status: 400 }
      );
    }

    if (!VAPI_API_KEY || !VAPI_DEFAULT_ASSISTANT_ID) {
      return NextResponse.json(
        { error: "Vapi configuration missing" },
        { status: 500 }
      );
    }

    if (mode === "web") {
      // Return payload for frontend web SDK
      const startPayload = {
        assistantId: VAPI_DEFAULT_ASSISTANT_ID,
        customerId: customerId,
        metadata: {
          customerId: customerId,
          mode: "web",
          timestamp: new Date().toISOString(),
        },
      };

      return NextResponse.json({
        mode: "web",
        startPayload,
        success: true,
      });
    } else {
      // Phone mode - trigger server-side call
      const callResponse = await fetch("https://api.vapi.ai/call/phone", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${VAPI_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          assistantId: VAPI_DEFAULT_ASSISTANT_ID,
          customer: {
            number: phoneNumber,
          },
          metadata: {
            customerId: customerId,
            mode: "phone",
            timestamp: new Date().toISOString(),
          },
        }),
      });

      if (!callResponse.ok) {
        const errorData = await callResponse.json().catch(() => ({}));
        return NextResponse.json(
          {
            error: "Failed to initiate phone call",
            details: errorData,
          },
          { status: callResponse.status }
        );
      }

      const callData = await callResponse.json();

      // Store callId -> customerId mapping in our backend
      try {
        await fetch(`${MEMORY_SERVICE_URL}/voice/mapping`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            callId: callData.id,
            customerId: customerId,
            mode: "phone",
            phoneNumber: phoneNumber,
          }),
        });
      } catch (mappingError) {
        console.error("Failed to store call mapping:", mappingError);
        // Continue anyway - the call was initiated successfully
      }

      return NextResponse.json({
        mode: "phone",
        callId: callData.id,
        status: callData.status,
        success: true,
      });
    }
  } catch (error) {
    console.error("Voice start error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
