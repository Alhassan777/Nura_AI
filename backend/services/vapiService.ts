import Vapi from '@vapi-ai/web';
import { getClientVapiConfig } from '@/utils/vapi-config';

// Define types for the JSON metadata
export interface EmotionalMetadata {
  // Required fields based on submit_reflection tool
  transcript: string;
  scene_title: string;
  ground_emotion: string;
  metaphor_prompt: string;
  
  // Optional fields
  body_locus?: string;
  sketch_shape?: string;
  temporal_tag?: 'new' | 'familiar';
  color_palette?: string[];
  sketch_motion?: string;
  cognitive_load?: string;
  temp_descriptor?: string;
  scene_description?: string;
  texture_descriptor?: string;
}

class VapiService {
  private vapi: any;
  private assistantId: string;
  
  constructor() {
    const config = getClientVapiConfig();
    this.vapi = new Vapi(config.publicKey);
    this.assistantId = config.defaultAssistantId;
  }

  startCall(): Promise<any> {
    return this.vapi.start(this.assistantId);
  }

  stopCall(): void {
    this.vapi.stop();
  }

  isMuted(): boolean {
    return this.vapi.isMuted();
  }

  setMuted(muted: boolean): void {
    this.vapi.setMuted(muted);
  }

  say(message: string, endCallAfterSpoken: boolean = false): void {
    this.vapi.say(message, endCallAfterSpoken);
  }

  sendMessage(content: string, role: 'system' | 'user' = 'system'): void {
    this.vapi.send({
      type: 'add-message',
      message: {
        role,
        content,
      },
    });
  }

  // Validate emotional metadata
  validateEmotionalMetadata(data: any): EmotionalMetadata | null {
    const requiredFields = ['transcript', 'scene_title', 'ground_emotion', 'metaphor_prompt'];
    
    // Check for required fields
    for (const field of requiredFields) {
      if (!data[field]) {
        console.error(`Missing required field ${field} in emotional metadata`);
        return null;
      }
    }
    
    // Cast to EmotionalMetadata type
    return data as EmotionalMetadata;
  }

  // Add event listeners
  onCallStart(callback: () => void): void {
    this.vapi.on('call-start', callback);
  }

  onCallEnd(callback: () => void): void {
    this.vapi.on('call-end', callback);
  }

  onSpeechStart(callback: () => void): void {
    this.vapi.on('speech-start', callback);
  }

  onSpeechEnd(callback: () => void): void {
    this.vapi.on('speech-end', callback);
  }

  onVolumeLevel(callback: (volume: number) => void): void {
    this.vapi.on('volume-level', callback);
  }

  onMessage(callback: (message: any) => void): void {
    this.vapi.on('message', callback);
  }

  onError(callback: (error: Error) => void): void {
    this.vapi.on('error', callback);
  }
}

export default VapiService; 