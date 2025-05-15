import { NextRequest, NextResponse } from 'next/server';
import { CallProcessingService } from '@/services/callProcessingService';

// Get user ID from environment or use demo user
// In a real app with Auth0, you would get this from the session or token
const getUserId = () => {
  return process.env.DEFAULT_USER_ID || 'demo-user-123';
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const userId = getUserId();
    
    // Validate webhook signature if needed
    // const signature = request.headers.get('x-vapi-signature');
    
    console.log('Received webhook from Vapi:', body);
    
    // Process different webhook types
    switch (body.type) {
      case 'call.started':
        // Handle call started event
        // Just log it for now
        console.log('Call started:', body.callId);
        break;

      case 'call.ended':
        // Handle call ended event - this is where we should get the analyzed data
        console.log('Call ended:', body.callId);

        // Check if there's analysis data
        if (body.analysis) {
          await CallProcessingService.processCallData(body.analysis, userId);
        } else {
          console.warn('Call ended but no analysis data received');
          // Store raw data for debugging
          CallProcessingService.storeRawWebhookData(body, userId);
        }
        break;

      case 'message':
        // Handle new message
        console.log('New message in call:', body.callId);
        break;

      case 'transcription':
        // Handle transcription update
        console.log('Transcription update for call:', body.callId);
        break;

      default:
        console.log(`Unhandled webhook type: ${body.type}`);
        // Store raw data for unknown webhook types
        CallProcessingService.storeRawWebhookData(body, userId);
    }
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json(
      { error: 'Failed to process webhook' },
      { status: 500 }
    );
  }
} 