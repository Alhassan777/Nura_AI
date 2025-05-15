import { NextRequest, NextResponse } from 'next/server';
import VapiApiService from '@/services/vapiApiService';

interface Params {
  params: {
    callId: string;
  };
}

export async function GET(request: NextRequest, { params }: Params) {
  try {
    const { callId } = params;
    
    if (!callId) {
      return NextResponse.json(
        { error: 'Call ID is required' },
        { status: 400 }
      );
    }
    
    const vapiService = new VapiApiService();
    const call = await vapiService.getCall(callId);
    
    return NextResponse.json(call);
  } catch (error) {
    console.error(`Failed to fetch call ${params.callId}:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch call details' },
      { status: 500 }
    );
  }
} 