import { NextRequest, NextResponse } from 'next/server';
import VapiApiService from '@/services/vapiApiService';

export async function GET() {
  try {
    const vapiService = new VapiApiService();
    const assistants = await vapiService.listAssistants();
    
    return NextResponse.json({ assistants });
  } catch (error) {
    console.error('Failed to fetch assistants:', error);
    return NextResponse.json(
      { error: 'Failed to fetch assistants' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { assistantId, customerPhone, customerName, callName } = body;
    
    if (!assistantId || !customerPhone) {
      return NextResponse.json(
        { error: 'assistantId and customerPhone are required' },
        { status: 400 }
      );
    }
    
    const vapiService = new VapiApiService();
    
    const call = await vapiService.createCall({
      assistantId,
      customer: {
        number: customerPhone,
        name: customerName,
      },
      name: callName || `Call to ${customerName || customerPhone}`,
    });
    
    return NextResponse.json(call);
  } catch (error) {
    console.error('Failed to create call:', error);
    return NextResponse.json(
      { error: 'Failed to create call' },
      { status: 500 }
    );
  }
} 