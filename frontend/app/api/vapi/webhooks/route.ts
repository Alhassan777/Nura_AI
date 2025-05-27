import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const VAPI_SERVER_SECRET = process.env.VAPI_SERVER_SECRET;
const MEMORY_SERVICE_URL =
  process.env.MEMORY_SERVICE_URL || "http://localhost:8000";

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
    const body = await request.text();
    let webhookEvent: VapiWebhookEvent;

    try {
      webhookEvent = JSON.parse(body);
    } catch (parseError) {
      console.error("Invalid JSON in webhook:", parseError);
      return NextResponse.json(
        { error: "Invalid JSON payload" },
        { status: 400 }
      );
    }

    // Validate HMAC signature if secret is configured
    if (
      VAPI_SERVER_SECRET &&
      VAPI_SERVER_SECRET !== "your_webhook_secret_here"
    ) {
      const signature =
        request.headers.get("X-Vapi-Signature") ||
        request.headers.get("x-vapi-signature");

      if (!signature) {
        console.error("Missing signature header");
        return NextResponse.json(
          { error: "Missing signature header" },
          { status: 401 }
        );
      }

      if (!validateSignature(body, signature, VAPI_SERVER_SECRET)) {
        console.error("Invalid signature");
        return NextResponse.json(
          { error: "Invalid signature" },
          { status: 401 }
        );
      }
    }

    // Log all webhook events for debugging
    console.log(
      `📞 Vapi Webhook: ${webhookEvent.type || webhookEvent.eventType}`,
      {
        eventType: webhookEvent.type || webhookEvent.eventType,
        callId: webhookEvent.call?.id || webhookEvent.callId || webhookEvent.id,
        timestamp: new Date().toISOString(),
      }
    );

    // Check if this is a conversation-update event that should be processed
    if (!shouldProcessEvent(webhookEvent)) {
      console.log(
        `⏭️  Ignoring ${
          webhookEvent.type || webhookEvent.eventType
        } event (not conversation-update)`
      );
      return NextResponse.json(
        {
          message: "Event received but not processed",
          eventType: webhookEvent.type || webhookEvent.eventType,
          processed: false,
        },
        { status: 200 }
      );
    }

    // Extract call ID for processing
    const callId =
      webhookEvent.call?.id || webhookEvent.callId || webhookEvent.id;
    if (!callId) {
      console.error(
        "No call ID found in conversation-update event:",
        webhookEvent
      );
      return NextResponse.json(
        { error: "No call ID found in event" },
        { status: 400 }
      );
    }

    // Forward to backend voice worker for processing
    try {
      const workerResponse = await fetch(
        `${MEMORY_SERVICE_URL}/voice/webhook-event`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            event: webhookEvent,
            callId: callId,
            receivedAt: new Date().toISOString(),
            source: "vapi_webhook",
          }),
        }
      );

      if (!workerResponse.ok) {
        const errorText = await workerResponse.text();
        console.error(
          `Backend processing failed: ${workerResponse.status} - ${errorText}`
        );

        // Still return 200 to Vapi to avoid retries for our internal errors
        return NextResponse.json(
          {
            message: "Event received but backend processing failed",
            error: errorText,
            eventType: webhookEvent.type || webhookEvent.eventType,
            processed: false,
          },
          { status: 200 }
        );
      }

      const result = await workerResponse.json();
      console.log(
        `✅ Successfully processed conversation-update for call ${callId}`
      );

      return NextResponse.json(
        {
          message: "Event processed successfully",
          eventType: webhookEvent.type || webhookEvent.eventType,
          callId: callId,
          processed: true,
          result: result,
        },
        { status: 200 }
      );
    } catch (forwardError) {
      console.error("Error forwarding to backend:", forwardError);

      // Still return 200 to Vapi to avoid retries
      return NextResponse.json(
        {
          message: "Event received but backend unavailable",
          eventType: webhookEvent.type || webhookEvent.eventType,
          processed: false,
        },
        { status: 200 }
      );
    }
  } catch (error) {
    console.error("Webhook processing error:", error);

    // Return 200 to avoid Vapi retries for our internal errors
    return NextResponse.json(
      {
        message: "Event received but processing failed",
        error: error instanceof Error ? error.message : String(error),
        processed: false,
      },
      { status: 200 }
    );
  }
}

// Health check endpoint
export async function GET(request: NextRequest) {
  return NextResponse.json({
    status: "healthy",
    message: "Vapi webhook endpoint is running",
    timestamp: new Date().toISOString(),
    config: {
      hasSecret:
        !!VAPI_SERVER_SECRET &&
        VAPI_SERVER_SECRET !== "your_webhook_secret_here",
      backendUrl: MEMORY_SERVICE_URL,
    },
  });
}
