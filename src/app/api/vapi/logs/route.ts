import { NextRequest, NextResponse } from 'next/server';
import VapiApiService from '@/services/vapiApiService';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const callId = searchParams.get('callId');
    const limit = searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined;
    const offset = searchParams.get('offset') ? Number(searchParams.get('offset')) : undefined;
    const startDate = searchParams.get('startDate') || undefined;
    const endDate = searchParams.get('endDate') || undefined;
    
    if (!callId) {
      return NextResponse.json(
        { error: 'callId parameter is required' },
        { status: 400 }
      );
    }
    
    const vapiService = new VapiApiService();
    const logs = await vapiService.getLogs({
      callId,
      limit,
      offset,
      startDate,
      endDate,
    });
    
    return NextResponse.json({ logs });
  } catch (error) {
    console.error('Failed to fetch logs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch logs' },
      { status: 500 }
    );
  }
} 