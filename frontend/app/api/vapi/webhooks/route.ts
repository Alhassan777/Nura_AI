import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const VAPI_SERVER_SECRET = process.env.VAPI_SERVER_SECRET || "";
const BACKEND_VOICE_URL =
  process.env.BACKEND_VOICE_URL || "http://localhost:8000";

interface VapiWebhookEvent {
  type: string;
  eventType?: string;
  call?: {
    id: string;
    status?: string;
  };
  callId?: string;
  id?: string;
  message?: {
    role: string;
    content: string;
  };
  timestamp?: string;
  [key: string]: any;
}

/**
 * Validate HMAC signature from Vapi webhook
 */
function validateSignature(
  body: string,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) {
    return false;
  }

  try {
    // Remove 'sha256=' prefix if present
    const cleanSignature = signature.replace(/^sha256=/, "");

    // Create HMAC
    const hmac = crypto.createHmac("sha256", secret);
    hmac.update(body, "utf8");
    const calculatedSignature = hmac.digest("hex");

    // Constant time comparison to prevent timing attacks
    return crypto.timingSafeEqual(
      Buffer.from(cleanSignature, "hex"),
      Buffer.from(calculatedSignature, "hex")
    );
  } catch (error) {
    console.error("Signature validation error:", error);
    return false;
  }
}

/**
 * Check if event should be processed (conversation-update events only)
 */
function shouldProcessEvent(event: VapiWebhookEvent): boolean {
  const eventType = event.type || event.eventType;
  return eventType === "conversation-update";
}

export async function POST(request: NextRequest) {
  try {
    // Get the raw body and signature
    const body = await request.text();
    const signature = request.headers.get("x-vapi-signature") || "";

    // Verify HMAC signature (optional security check before forwarding)
    if (VAPI_SERVER_SECRET) {
      const expectedSignature = crypto
        .createHmac("sha256", VAPI_SERVER_SECRET)
        .update(body, "utf8")
        .digest("hex");

      if (
        !crypto.timingSafeEqual(
          Buffer.from(signature.replace("sha256=", ""), "hex"),
          Buffer.from(expectedSignature, "hex")
        )
      ) {
        console.error("Invalid webhook signature");
        return NextResponse.json(
          { error: "Invalid signature" },
          { status: 401 }
        );
      }
    }

    // Parse the webhook payload
    const payload = JSON.parse(body);

    // Only process conversation-related events
    const eventType = payload.type || payload.eventType;
    if (!["call-start", "call-end", "analysis-complete"].includes(eventType)) {
      console.log(`Ignoring event type: ${eventType}`);
      return NextResponse.json({ status: "ignored" }, { status: 200 });
    }

    console.log(`Processing webhook event: ${eventType}`);

    // Forward to backend voice service
    const backendResponse = await fetch(`${BACKEND_VOICE_URL}/voice/webhook`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-vapi-signature": signature,
      },
      body: body,
    });

    if (!backendResponse.ok) {
      console.error(`Backend processing failed: ${backendResponse.status}`);
      // Still return 200 to Vapi to avoid retries
      return NextResponse.json(
        {
          status: "error",
          message: "Backend processing failed",
        },
        { status: 200 }
      );
    }

    const result = await backendResponse.json();
    console.log(`Webhook processed successfully: ${eventType}`);

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    console.error("Webhook processing error:", error);

    // Always return 200 to Vapi to avoid retries
    return NextResponse.json(
      {
        status: "error",
        message: "Internal processing error",
      },
      { status: 200 }
    );
  }
}

// Health check endpoint
export async function GET() {
  return NextResponse.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
    service: "webhook-handler",
  });
}
