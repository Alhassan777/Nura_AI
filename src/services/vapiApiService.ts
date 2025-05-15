import axios from 'axios';
import { getVapiConfig } from '@/utils/vapi-config';

// Define API response types
export interface Call {
  id: string;
  status: string;
  startedAt?: string;
  endedAt?: string;
  type: string;
  cost?: number;
  costBreakdown?: {
    transport: number;
    stt: number;
    llm: number;
    tts: number;
    vapi: number;
    total: number;
  };
  messages?: Array<{
    role: string;
    message: string;
    time: number;
    endTime: number;
    duration: number;
  }>;
}

export interface Assistant {
  id: string;
  name: string;
  description?: string;
  model?: string;
  voice?: {
    provider: string;
    voiceId: string;
  };
}

export interface Log {
  id: string;
  callId: string;
  timestamp: string;
  type: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: string;
  config?: Record<string, any>;
}

class VapiApiService {
  private api: ReturnType<typeof axios.create>;
  
  constructor() {
    const { apiKey } = getVapiConfig();
    
    this.api = axios.create({
      baseURL: 'https://api.vapi.ai',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  // Calls API
  async createCall(options: {
    assistantId?: string;
    assistant?: Record<string, any>;
    customer?: {
      number: string;
      name?: string;
    };
    name?: string;
  }): Promise<Call> {
    const response = await this.api.post('/call', options);
    return response.data;
  }

  async getCall(callId: string): Promise<Call> {
    const response = await this.api.get(`/call/${callId}`);
    return response.data;
  }

  // Assistants API
  async getAssistant(assistantId: string): Promise<Assistant> {
    const response = await this.api.get(`/assistant/${assistantId}`);
    return response.data;
  }

  async listAssistants(): Promise<Assistant[]> {
    const response = await this.api.get('/assistant');
    return response.data.assistants;
  }

  // Logs API
  async getLogs(options: {
    callId?: string;
    limit?: number;
    offset?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<Log[]> {
    const response = await this.api.get('/logs', { params: options });
    return response.data.logs;
  }

  // Tools API
  async getTool(toolId: string): Promise<Tool> {
    const response = await this.api.get(`/tool/${toolId}`);
    return response.data;
  }

  async listTools(): Promise<Tool[]> {
    const response = await this.api.get('/tool');
    return response.data.tools;
  }
}

export default VapiApiService; 